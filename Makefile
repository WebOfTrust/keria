.PHONY: build-keria
build-keria:
	@docker build --platform=linux/amd64,linux/arm64 --no-cache -f images/keria.dockerfile --tag m00sey/keria:0.2.0-dev4-sig-fix .

publish-keria:
	@docker push m00sey/keria:0.2.0-dev4-sig-fix
