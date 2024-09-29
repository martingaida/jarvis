build-PythonLayer:
	@echo "Current directory: $$(pwd)"
	@echo "ARTIFACTS_DIR: $(ARTIFACTS_DIR)"
	./build-layer.sh
	@echo "Contents of current directory after build-layer.sh:"
	@ls -l
	mv python.zip $(ARTIFACTS_DIR)/
	@echo "Contents of ARTIFACTS_DIR after move:"
	@ls -l $(ARTIFACTS_DIR)/

build-DataLambda:
	cp -r data $(ARTIFACTS_DIR)

build-TranscribeLambda:
	cp -r transcribe $(ARTIFACTS_DIR)

build-EnhanceLambda:
	cp -r enhance $(ARTIFACTS_DIR)

build-StoreLambda:
	cp -r store $(ARTIFACTS_DIR)