.PHONY: build-keria
build-keria:
	@docker build --no-cache -f images/keria.dockerfile --tag weboftrust/keria:0.0.1 .

publish-keria:
	@docker push weboftrust/keria:0.0.1