#!/bin/bash

find lparse-1.1.2/src -type f -print0 | xargs -0 sed -i -r 's/([( ])hash\(/\1_hash(/g'
find lparse-1.1.2/src -type f -print0 | xargs -0 sed -i -r 's/runtime_error/_runtime_error/g'

