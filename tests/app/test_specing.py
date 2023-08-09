import json

from keria.app import agenting, aiding, notifying, indirecting, specing
from keria.end import ending


def test_spec_resource(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        # Add all the endpoints similar to the agenting.setup function
        agenting.loadEnds(app)
        aiding.loadEnds(app, agency, authn=None)
        notifying.loadEnds(app)
        ending.loadEnds(agency=agency, app=app)
        indirecting.loadEnds(agency=agency, app=app)

        specRes = specing.AgentSpecResource(app, title='KERIA Interactive Web Interface API')

        sd = specRes.spec.to_dict()

        assert "paths" in sd
        paths = sd["paths"]
        assert "/" in paths
        assert "/agent/{caid}" in paths
        assert "/challenges" in paths
        assert "/challenges/{name}" in paths
        assert "/contacts/{prefix}" in paths
        assert "/contacts/{prefix}/img" in paths
        assert "/events" in paths
        assert "/identifiers" in paths
        assert "/identifiers/{name}" in paths
        assert "/identifiers/{name}/endroles" in paths
        assert "/identifiers/{name}/oobis" in paths
        assert "/notifications" in paths
        assert "/notifications/{said}" in paths
        assert "/oobi" in paths
        assert "/oobi/{aid}" in paths
        assert "/oobi/{aid}/{role}" in paths
        assert "/oobi/{aid}/{role}/{eid}" in paths
        assert "/oobis" in paths
        assert "/oobis/{alias}" in paths
        assert "/operations/{name}" in paths
        assert "/queries" in paths
        assert "/states" in paths

        js = json.dumps(sd)

        # Assert on the entire JSON to ensure we are getting all the docs
        assert js == ('{"paths": {"/oobis": {"post": {"summary": "Resolve OOBI and assign an alias '
                      'for the remote identifier", "description": "Resolve OOBI URL or `rpy` '
                      "message by process results of request and assign 'alias' in contact data for "
                      'resolved identifier", "tags": ["OOBIs"], "requestBody": {"required": true, '
                      '"content": {"application/json": {"schema": {"description": "OOBI", '
                      '"properties": {"oobialias": {"type": "string", "description": "alias to '
                      'assign to the identifier resolved from this OOBI", "required": false}, '
                      '"url": {"type": "string", "description": "URL OOBI"}, "rpy": {"type": '
                      '"object", "description": "unsigned KERI `rpy` event message with '
                      'endpoints"}}}}}}, "responses": {"202": {"description": "OOBI resolution to '
                      'key state successful"}}}}, "/states": {"get": {"summary": "Display key event '
                      'log (KEL) for given identifier prefix", "description": "If provided qb64 '
                      'identifier prefix is in Kevers, return the current state of the identifier '
                      'along with the KEL and all associated signatures and receipts", "tags": '
                      '["Key Event Log"], "parameters": [{"in": "path", "name": "prefix", "schema": '
                      '{"type": "string"}, "required": true, "description": "qb64 identifier prefix '
                      'of KEL to load"}], "responses": {"200": {"description": "Key event log and '
                      'key state of identifier"}, "404": {"description": "Identifier not found in '
                      'Key event database"}}}}, "/events": {"get": {"summary": "Display key event '
                      'log (KEL) for given identifier prefix", "description": "If provided qb64 '
                      'identifier prefix is in Kevers, return the current state of the identifier '
                      'along with the KEL and all associated signatures and receipts", "tags": '
                      '["Key Event Log"], "parameters": [{"in": "path", "name": "prefix", "schema": '
                      '{"type": "string"}, "required": true, "description": "qb64 identifier prefix '
                      'of KEL to load"}], "responses": {"200": {"description": "Key event log and '
                      'key state of identifier"}, "404": {"description": "Identifier not found in '
                      'Key event database"}}}}, "/queries": {"post": {"summary": "Display key event '
                      'log (KEL) for given identifier prefix", "description": "If provided qb64 '
                      'identifier prefix is in Kevers, return the current state of the identifier '
                      'along with the KEL and all associated signatures and receipts", "tags": '
                      '["Query"], "parameters": [{"in": "body", "name": "pre", "schema": {"type": '
                      '"string"}, "required": true, "description": "qb64 identifier prefix of KEL '
                      'to load"}], "responses": {"200": {"description": "Key event log and key '
                      'state of identifier"}, "404": {"description": "Identifier not found in Key '
                      'event database"}}}}, "/identifiers": {"get": {}, "options": {}, "post": {}}, '
                      '"/challenges": {"get": {"summary": "Get list of agent identifiers", '
                      '"description": "Get the list of identifiers associated with this agent", '
                      '"tags": ["Challenge/Response"], "parameters": [{"in": "query", "name": '
                      '"strength", "schema": {"type": "int"}, "description": "cryptographic '
                      'strength of word list", "required": false}], "responses": {"200": '
                      '{"description": "An array of Identifier key state information", "content": '
                      '{"application/json": {"schema": {"description": "Randon word list", "type": '
                      '"object", "properties": {"words": {"type": "array", "description": "random '
                      'challange word list", "items": {"type": "string"}}}}}}}}}}, "/contacts": '
                      '{"get": {"summary": "Get list of contact information associated with remote '
                      'identifiers", "description": "Get list of contact information associated '
                      'with remote identifiers.  All information is metadata and kept in local '
                      'storage only", "tags": ["Contacts"], "parameters": [{"in": "query", "name": '
                      '"group", "schema": {"type": "string"}, "required": false, "description": '
                      '"field name to group results by"}, {"in": "query", "name": "filter_field", '
                      '"schema": {"type": "string"}, "description": "field name to search", '
                      '"required": false}, {"in": "query", "name": "filter_value", "schema": '
                      '{"type": "string"}, "description": "value to search for", "required": '
                      'false}], "responses": {"200": {"description": "List of contact information '
                      'for remote identifiers"}}}}, "/notifications": {"get": {"summary": "Get list '
                      'of notifcations for the controller of the agent", "description": "Get list '
                      'of notifcations for the controller of the agent.  Notifications will be '
                      'sorted by creation date/time", "parameters": [{"in": "query", "name": '
                      '"last", "schema": {"type": "string"}, "required": false, "description": '
                      '"qb64 SAID of last notification seen"}, {"in": "query", "name": "limit", '
                      '"schema": {"type": "integer"}, "required": false, "description": "size of '
                      'the result list.  Defaults to 25"}], "tags": ["Notifications"], "responses": '
                      '{"200": {"description": "List of contact information for remote '
                      'identifiers"}}}}, "/oobi": {"get": {}}, "/": {"post": {"summary": "Accept '
                      'KERI events with attachment headers and parse", "description": "Accept KERI '
                      'events with attachment headers and parse.", "tags": ["Events"], '
                      '"requestBody": {"required": true, "content": {"application/json": {"schema": '
                      '{"type": "object", "description": "KERI event message"}}}}, "responses": '
                      '{"204": {"description": "KEL EXN, QRY, RPY event accepted."}}}}, '
                      '"/operations/{name}": {"delete": {}, "get": {}}, "/oobis/{alias}": {"get": '
                      '{"summary": "Get OOBI for specific identifier", "description": "Generate '
                      'OOBI for the identifier of the specified alias and role", "tags": ["OOBIs"], '
                      '"parameters": [{"in": "path", "name": "alias", "schema": {"type": "string"}, '
                      '"required": true, "description": "human readable alias for the identifier '
                      'generate OOBI for"}, {"in": "query", "name": "role", "schema": {"type": '
                      '"string"}, "required": true, "description": "role for which to generate '
                      'OOBI"}], "responses": {"200": {"description": "An array of Identifier key '
                      'state information", "content": {"application/json": {"schema": '
                      '{"description": "Key state information for current identifiers", "type": '
                      '"object"}}}}}}}, "/agent/{caid}": {"get": {}, "put": {}}, '
                      '"/identifiers/{name}": {"get": {}, "put": {}}, "/endroles/{aid}": {"get": '
                      '{}, "post": {}}, "/escrows/rpy": {"get": {}}, "/challenges/{name}": {"post": '
                      '{"summary": "Sign challange message and forward to peer identfiier", '
                      '"description": "Sign a challenge word list received out of bands and send '
                      '`exn` peer to peer message to recipient", "tags": ["Challenge/Response"], '
                      '"parameters": [{"in": "path", "name": "name", "schema": {"type": "string"}, '
                      '"required": true, "description": "Human readable alias for the identifier to '
                      'create"}], "requestBody": {"required": true, "content": {"application/json": '
                      '{"schema": {"description": "Challenge response", "properties": {"recipient": '
                      '{"type": "string", "description": "human readable alias recipient identifier '
                      'to send signed challenge to"}, "words": {"type": "array", "description": '
                      '"challenge in form of word list", "items": {"type": "string"}}}}}}}, '
                      '"responses": {"202": {"description": "Success submission of signed '
                      'challenge/response"}}}, "put": {"summary": "Mark challenge response exn '
                      'message as signed", "description": "Mark challenge response exn message as '
                      'signed", "tags": ["Challenge/Response"], "parameters": [{"in": "path", '
                      '"name": "name", "schema": {"type": "string"}, "required": true, '
                      '"description": "Human readable alias for the identifier to create"}], '
                      '"requestBody": {"required": true, "content": {"application/json": {"schema": '
                      '{"description": "Challenge response", "properties": {"aid": {"type": '
                      '"string", "description": "aid of signer of accepted challenge response"}, '
                      '"said": {"type": "array", "description": "SAID of challenge message signed", '
                      '"items": {"type": "string"}}}}}}}, "responses": {"202": {"description": '
                      '"Success submission of signed challenge/response"}}}}, "/contacts/{prefix}": '
                      '{"delete": {"summary": "Delete contact information associated with remote '
                      'identfier", "description": "Delete contact information associated with '
                      'remote identfier", "tags": ["Contacts"], "parameters": [{"in": "path", '
                      '"name": "prefix", "schema": {"type": "string"}, "required": true, '
                      '"description": "qb64 identifier prefix of contact to delete"}], "responses": '
                      '{"202": {"description": "Contact information successfully deleted for '
                      'prefix"}, "404": {"description": "No contact information found for '
                      'prefix"}}}, "get": {"summary": "Get contact information associated with '
                      'single remote identfier", "description": "Get contact information associated '
                      'with single remote identfier.  All information is meta-data and kept in '
                      'local storage only", "tags": ["Contacts"], "parameters": [{"in": "path", '
                      '"name": "prefix", "schema": {"type": "string"}, "required": true, '
                      '"description": "qb64 identifier prefix of contact to get"}], "responses": '
                      '{"200": {"description": "Contact information successfully retrieved for '
                      'prefix"}, "404": {"description": "No contact information found for '
                      'prefix"}}}, "post": {"summary": "Create new contact information for an '
                      'identifier", "description": "Creates new information for an identifier, '
                      'overwriting all existing information for that identifier", "tags": '
                      '["Contacts"], "parameters": [{"in": "path", "name": "prefix", "schema": '
                      '{"type": "string"}, "required": true, "description": "qb64 identifier prefix '
                      'to add contact metadata to"}], "requestBody": {"required": true, "content": '
                      '{"application/json": {"schema": {"description": "Contact information", '
                      '"type": "object"}}}}, "responses": {"200": {"description": "Updated contact '
                      'information for remote identifier"}, "400": {"description": "Invalid '
                      'identfier used to update contact information"}, "404": {"description": '
                      '"Prefix not found in identifier contact information"}}}, "put": {"summary": '
                      '"Update provided fields in contact information associated with remote '
                      'identfier prefix", "description": "Update provided fields in contact '
                      'information associated with remote identfier prefix.  All information is '
                      'metadata and kept in local storage only", "tags": ["Contacts"], '
                      '"parameters": [{"in": "path", "name": "prefix", "schema": {"type": '
                      '"string"}, "required": true, "description": "qb64 identifier prefix to add '
                      'contact metadata to"}], "requestBody": {"required": true, "content": '
                      '{"application/json": {"schema": {"description": "Contact information", '
                      '"type": "object"}}}}, "responses": {"200": {"description": "Updated contact '
                      'information for remote identifier"}, "400": {"description": "Invalid '
                      'identfier used to update contact information"}, "404": {"description": '
                      '"Prefix not found in identifier contact information"}}}}, '
                      '"/notifications/{said}": {"delete": {"summary": "Delete notification", '
                      '"description": "Delete notification", "tags": ["Notifications"], '
                      '"parameters": [{"in": "path", "name": "said", "schema": {"type": "string"}, '
                      '"required": true, "description": "qb64 said of note to delete"}], '
                      '"responses": {"202": {"description": "Notification successfully deleted for '
                      'prefix"}, "404": {"description": "No notification information found for '
                      'prefix"}}}, "put": {"summary": "Mark notification as read", "description": '
                      '"Mark notification as read", "tags": ["Notifications"], "parameters": '
                      '[{"in": "path", "name": "said", "schema": {"type": "string"}, "required": '
                      'true, "description": "qb64 said of note to mark as read"}], "responses": '
                      '{"202": {"description": "Notification successfully marked as read for '
                      'prefix"}, "404": {"description": "No notification information found for '
                      'SAID"}}}}, "/oobi/{aid}": {"get": {}}, "/identifiers/{name}/oobis": {"get": '
                      '{}}, "/identifiers/{name}/endroles": {"get": {}, "post": {}}, '
                      '"/identifiers/{name}/members": {"get": {}}, "/endroles/{aid}/{role}": '
                      '{"get": {}, "post": {}}, "/contacts/{prefix}/img": {"get": {"summary": "Get '
                      'contact image for identifer prefix", "description": "Get contact image for '
                      'identifer prefix", "tags": ["Contacts"], "parameters": [{"in": "path", '
                      '"name": "prefix", "schema": {"type": "string"}, "required": true, '
                      '"description": "qb64 identifier prefix of contact image to get"}], '
                      '"responses": {"200": {"description": "Contact information successfully '
                      'retrieved for prefix", "content": {"image/jpg": {"schema": {"description": '
                      '"Image", "type": "binary"}}}}, "404": {"description": "No contact '
                      'information found for prefix"}}}, "post": {"summary": "Uploads an image to '
                      'associate with identfier.", "description": "Uploads an image to associate '
                      'with identfier.", "tags": ["Contacts"], "parameters": [{"in": "path", '
                      '"name": "prefix", "schema": {"type": "string"}, "description": "identifier '
                      'prefix to associate image to", "required": true}], "requestBody": '
                      '{"required": true, "content": {"image/jpg": {"schema": {"type": "string", '
                      '"format": "binary"}}, "image/png": {"schema": {"type": "string", "format": '
                      '"binary"}}}}, "responses": {"200": {"description": "Image successfully '
                      'uploaded"}}}}, "/oobi/{aid}/{role}": {"get": {}}, '
                      '"/identifiers/{name}/endroles/{role}": {"get": {}, "post": {}}, '
                      '"/oobi/{aid}/{role}/{eid}": {"get": {}}, '
                      '"/identifiers/{name}/endroles/{role}/{eid}": {"delete": {}}}, "info": '
                      '{"title": "KERIA Interactive Web Interface API", "version": "1.0.1"}, '
                      '"openapi": "3.1.0"}')
