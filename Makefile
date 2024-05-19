.PHONY: build-keria
build-keria:
	@docker buildx build --platform=linux/amd64 --no-cache -f images/keria.dockerfile --tag weboftrust/keria:0.2.0-dev1 .

publish-keria:
	@docker push weboftrust/keria --all-tags