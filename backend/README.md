# Hetida Designer Backend

The hetida designer backend is the hetida designer sub-module that provides the REST API for data retrieval and persistence of different structures, configurations and settings.The hetida designer frontend communicates directly with the hetida designer backend for this purpose.

The heitda designer backend is not intended for use by other clients than the hetida designer frontend

## API Documentation  
The endpoints of the provided REST API are documented via Swagger. You can open the Swagger UI at: 
`<base-url>/hdapi/v2/api-docs` 
which in development often will be
`http://localhost/hdapi/v2/api-docs`

## Development Setup
Dependencies: OpenJDK 1.8 and a recent version of maven.

The backend is a Spring Boot application and can be started in your IDE locally
in the usual way by adding following parameters to your run configuration:

1. `spring.datasource.url=jdbc:postgresql://localhost:5430/hetida_designer_db`
2. `org.hetida.designer.backend.codegen=http://localhost:8090/codegen`
3. `org.hetida.designer.backend.codecheck=http://localhost:8090/codecheck`
4. `org.hetida.designer.backend.runtime=http://localhost:8090/runtime`

or using maven:

1. Navigate to the `backend` folder.
2. Run `mvn clean package` to build the application.
3. Run the Spring Boot application with maven `mvn spring-boot:run -Dspring.datasource.url="jdbc:postgresql://localhost:5430/hetida_designer_db" -Dorg.hetida.designer.backend.codegen="http://localhost:8090/codegen" -Dorg.hetida.designer.backend.codecheck="http://localhost:8090/codecheck" -Dorg.hetida.designer.backend.runtime="http://localhost:8090/runtime"`.

To run the tests:
1. Navigate to the `backend` folder.
2. Run `mvn test`.

## Dependency Management

The dependencies are managed via maven. Take a look at the pom.xml file to get an overview of all needed dependencies.

 
