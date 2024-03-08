.PHONY: build-keria
build-keria:
	@docker buildx build --platform=linux/amd64 --no-cache -f images/keria.dockerfile --tag weboftrust/keria:0.1.3  --tag weboftrust/keria:latest .

publish-keria:
	@docker push weboftrust/keria --all-tags