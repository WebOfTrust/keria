.PHONY: build-keria
build-keria:
	@docker buildx build --platform=linux/amd64 --no-cache -f images/keria.dockerfile --tag 2byrds/keria:0.3.0-dev1 .

publish-keria:
	@docker push 2byrds/keria --all-tags