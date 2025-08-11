# /****************************************************************************************/
# Copyright (c) 2025 LearnAnythingWithAI. All Rights Reserved.
# /****************************************************************************************/
release: fetch release
debug: fetch debug


CWD = $(shell pwd | sed 's/^.*x64//')
MV=mv
RM=rm
MKDIR=mkdir
CP=cp
BUILD_DIR = $(CWD)/build

ifndef IMAGE_VERSION
export IMAGE_VERSION=v1.0.0
endif


fetch:


release:
	@echo "--->  Building LearnAnythingWithAI Docker Image"
	docker build -t mija2022/learn-anything-with-ai:$(IMAGE_VERSION) .

debug:
	@echo "--->  Building LearnAnythingWithAI Docker Image"
	docker build -t mija2022/learn-anything-with-ai:v_dbg .


mv-modules:

push_rls:
	docker push  mija2022/learn-anything-with-ai:$(IMAGE_VERSION)

push_dbg:
	docker push  mija2022/learn-anything-with-ai:v_dbg

clean:
	@[ -f main ] && rm -f main || true
	$(RM) -rf $(BUILD_DIR)
