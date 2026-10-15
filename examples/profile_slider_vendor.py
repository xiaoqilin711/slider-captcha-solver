"""Redacted profile for one commercial slider CAPTCHA vendor.

Everything that could identify the target is redacted:
  - the site domain          -> placeholder
  - the OCR endpoint + key   -> placeholders
  - the vendor's CSS class   -> a generic ".captcha-slider"
  - the vendor's API paths   -> generic "/captcha/get", "/captcha/check"

The *algorithmic* artifacts are kept verbatim because they carry no vendor
identity and are the reusable finding:
  - REFERENCE_DX / REFERENCE_DT / REFERENCE_DY  (a real human drag recording)
  - OFFSET  (calibrated correction: drag distance = gap left edge + OFFSET)

Fill in the redacted values for your own authorized target to run the demo.
"""

# --- redacted: target identity -------------------------------------------------
TARGET_URL = "https://www.example.com/thread/12345"

# --- redacted: vendor-specific CSS / API paths --------------------------------
SLIDER_SELECTOR = ".captcha-slider"          # real class redacted
GET_URL_SUBSTR = "/captcha/get"              # real path redacted
CHECK_URL_SUBSTR = "/captcha/check"          # real path redacted

# Field regexes operate on the JSONP body. "bg" is the background image URL.
BG_PATTERN = r'"bg":\["([^"]+)"'
RESULT_PATTERN = r'"result":(\w+)'
VALIDATE_PATTERN = r'"validate":"([^"]*)"'

# --- redacted: third-party OCR credentials -------------------------------------
OCR_URL = "https://ocr.example.com/predict"
KEY_CODE = "REDACTED"
QUESTION = "框出正确位置"          # OCR prompt, not sensitive
MODEL_NAME = "普通模型"            # OCR model name, not sensitive

# --- algorithmic artifacts (kept verbatim, reusable) ---------------------------
# Calibrated offset: drag distance = OCR gap left edge + OFFSET.
OFFSET = 10

# A real human drag, recorded on one target and normalized by sum(dx) == 129.
# Shape: fast sprint (~500 px/s) for the first third, then a slow fine-tune
# (~30 px/s) that nudges 0-1 px at a time near the gap. dt is per-step ms.
REFERENCE_DX = [1,1,2,2,4,4,4,4,4,5,5,5,5,7,5,5,6,4,5,4,3,2,2,1,1,1,1,1,1,1,2,1,3,1,2,2,1,2,0,1,2,1,1,1,1,1,1,1,1,1,0,1,0,1,0,1,1,0,1,0,0,1,0,1]
REFERENCE_DT = [46,7,9,8,9,8,8,9,8,8,9,8,8,8,9,8,9,8,8,8,9,8,9,8,8,9,8,8,8,9,8,9,8,8,8,9,8,8,9,8,8,9,8,8,9,8,8,9,8,9,8,8,8,9,9,15,74,8,10,12,5,50,16,178]
REFERENCE_DY = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0]
