---
description: Initialize the shell before running anything
---
{{ @language/init-shell-uv }} && export PROMPY_CONFIG_DIR=$(pwd)/sample-prompts && eval "$(_PROMPY_COMPLETE=bash_source prompy)"
