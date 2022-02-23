package org.hetida.designer.backend.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import springfox.documentation.builders.ApiInfoBuilder;
import springfox.documentation.builders.PathSelectors;
import springfox.documentation.builders.RequestHandlerSelectors;
import springfox.documentation.service.ApiInfo;
import springfox.documentation.spi.DocumentationType;
import springfox.documentation.spring.web.plugins.Docket;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

@Configuration
@EnableSwagger2
public class SwaggerConfig {

    @Bean
    public Docket api() {
        Docket d = new Docket(DocumentationType.SWAGGER_2)
                .select()
                .apis(RequestHandlerSelectors.basePackage("org.hetida.designer.backend.controller"))
                .paths(PathSelectors.any())
                .build().apiInfo(apiEndPointsInfo());

        return d;
    }

    private ApiInfo apiEndPointsInfo() {
        return new ApiInfoBuilder().title("Hetida designer REST API")
                .description("Use the hetida designer Backend with this REST API")
                .build();
    }
}

