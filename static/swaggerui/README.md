# KERI Interactive Web Interface API 
## OpenAPI spec (3.1.0) with SwaggerUI (5.0.0-alpha.9)

The contents of this directory, other than this Readme, are pulled from the 
[5.0.0-alpha.9 release](https://github.com/swagger-api/swagger-ui/releases/tag/v5.0.0-alpha.9) release page 
in the `/dist` directory of the downloadable .zip file.

## Upgrading
Go to the [swagger-ui releases](https://github.com/swagger-api/swagger-ui/releases) page, download the .zip file for the
release you want to upgrade to, extract the `/dist` directory contents, clear the `/static/swaggerui` contents in this 
repository, place the contents of `/dist` from the zip file into `/static/swaggerui` and then update the
`swagger-initializer.js` file to point to `spec.yaml` rather than `https://petstore.swagger.io/v2/swagger.json`.

## Notice on alpha version
The Swagger UI is an early alpha version and some things may be broken, though it has to do with the newest of features
so all the typical features likely work just fine. 

See [this article](https://www.openapis.org/blog/2021/02/16/migrating-from-openapi-3-0-to-3-1-0) for a comparison of 
OpenAPI 3.0.x and 3.1.0. That article also links to another article with an in depth explanation of the new features in
OpenAPI 3.1.0 and the changes from 3.0.x.
