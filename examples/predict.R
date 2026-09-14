#!/usr/bin/env Rscript

# Reference ITIH inference workflow for R and RStudio.

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2L || length(args) > 3L) {
  stop(
    "Usage: Rscript examples/predict.R INPUT.tsv OUTPUT.tsv [MODEL.cbm]",
    call. = FALSE
  )
}

if (!requireNamespace("catboost", quietly = TRUE)) {
  stop(
    "The CatBoost R package is required; see https://catboost.ai/docs/en/concepts/r-installation",
    call. = FALSE
  )
}
if (!requireNamespace("digest", quietly = TRUE)) {
  stop("Install the R package 'digest' to verify the model checksum.", call. = FALSE)
}

input_path <- args[[1L]]
output_path <- args[[2L]]
model_filename <- "itih_catboost_v1.cbm"
model_url <- paste0(
  "https://github.com/davidmascolo/ITIH/releases/download/v0.1.0/",
  model_filename
)
model_sha256 <- "d787a8ec308cace285541fbe76aefc3bbe9d2a545c9d3eabe93c87f4041af257"

if (length(args) == 3L) {
  model_path <- path.expand(args[[3L]])
} else {
  cache_dir <- if (getRversion() >= "4.0.0") {
    tools::R_user_dir("itih", which = "cache")
  } else {
    file.path(path.expand("~"), ".cache", "itih")
  }
  dir.create(cache_dir, recursive = TRUE, showWarnings = FALSE)
  model_path <- file.path(cache_dir, model_filename)
}

sha256 <- function(path) {
  tolower(digest::digest(file = path, algo = "sha256", serialize = FALSE))
}

if (!file.exists(model_path)) {
  dir.create(dirname(model_path), recursive = TRUE, showWarnings = FALSE)
  temporary_path <- tempfile(pattern = paste0(model_filename, "."), tmpdir = dirname(model_path))
  tryCatch(
    {
      message("Downloading the versioned ITIH model...")
      status <- utils::download.file(model_url, temporary_path, mode = "wb", quiet = FALSE)
      if (!identical(status, 0L)) {
        stop("The model download did not complete successfully.", call. = FALSE)
      }
      if (!identical(sha256(temporary_path), model_sha256)) {
        stop("Downloaded model checksum mismatch; the temporary file was discarded.", call. = FALSE)
      }
      if (!file.rename(temporary_path, model_path)) {
        stop("Could not move the verified model into the local cache.", call. = FALSE)
      }
    },
    finally = {
      if (file.exists(temporary_path)) {
        unlink(temporary_path)
      }
    }
  )
}

if (!identical(sha256(model_path), model_sha256)) {
  stop("Model checksum mismatch. Download the published v0.1.0 artifact again.", call. = FALSE)
}

feature_names <- c(
  "MHCI", "MHCII", "Coactivation_molecules", "Effector_cells",
  "T_cell_traffic", "NK_cells", "T_cells", "B_cells",
  "M1_signatures", "Th1_signature", "Antitumor_cytokines",
  "Checkpoint_inhibition", "Treg", "T_reg_traffic",
  "Neutrophil_signature", "Granulocyte_traffic", "MDSC",
  "MDSC_traffic", "Macrophages", "Macrophage_DC_traffic",
  "Th2_signature", "Protumor_cytokines", "CAF", "Matrix",
  "Matrix_remodeling", "Angiogenesis", "Endothelium",
  "Proliferation_rate", "EMT_signature"
)

scores <- utils::read.delim(input_path, check.names = FALSE, stringsAsFactors = FALSE)
if (!"sample_id" %in% names(scores)) {
  stop("Input must contain a 'sample_id' column.", call. = FALSE)
}
if (anyNA(scores$sample_id) || any(scores$sample_id == "") || anyDuplicated(scores$sample_id)) {
  stop("Sample identifiers must be present, non-empty and unique.", call. = FALSE)
}

observed_features <- setdiff(names(scores), "sample_id")
missing_features <- setdiff(feature_names, observed_features)
extra_features <- setdiff(observed_features, feature_names)
if (length(missing_features) || length(extra_features)) {
  stop(
    paste0(
      "Feature schema mismatch. Missing: ", paste(missing_features, collapse = ", "),
      "; unexpected: ", paste(extra_features, collapse = ", ")
    ),
    call. = FALSE
  )
}

x <- scores[, feature_names, drop = FALSE]
if (!all(vapply(x, is.numeric, logical(1L)))) {
  stop("All MFP feature values must be numeric.", call. = FALSE)
}
if (!all(vapply(x, function(column) all(is.finite(column)), logical(1L)))) {
  stop("MFP feature values cannot contain missing or infinite values.", call. = FALSE)
}

encode_score <- function(value) {
  factor(
    ifelse(value <= -0.75, "0", ifelse(value <= 0.75, "1", "2")),
    levels = c("0", "1", "2")
  )
}

x_binned <- as.data.frame(lapply(x, encode_score), check.names = FALSE)
pool <- catboost::catboost.load_pool(x_binned, feature_names = feature_names)
model <- catboost::catboost.load_model(model_path)
class_id <- as.integer(catboost::catboost.predict(model, pool, prediction_type = "Class"))

if (length(class_id) != nrow(scores) || any(!class_id %in% 0:3)) {
  stop("The model returned an unexpected class result.", call. = FALSE)
}

class_labels <- c("Hom-D", "Hom-IE", "Het-D", "Het-IE")
results <- data.frame(
  sample_id = scores$sample_id,
  class_id = class_id,
  itih_class = class_labels[class_id + 1L],
  check.names = FALSE
)

dir.create(dirname(output_path), recursive = TRUE, showWarnings = FALSE)
utils::write.table(results, output_path, sep = "\t", row.names = FALSE, quote = FALSE)
message("Wrote ", nrow(results), " predictions to ", output_path)
