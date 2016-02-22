#!/usr/bin/env bash
rsync -avz --del --exclude-from=data/excludes.txt ftp@ftp.ibiblio.org::gutenberg /media/$USER/nas/