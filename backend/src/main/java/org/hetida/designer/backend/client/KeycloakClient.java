package org.hetida.designer.backend.client;

import lombok.extern.log4j.Log4j2;
import org.hetida.designer.backend.dto.AccessTokenDTO;
import org.keycloak.OAuth2Constants;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;

import java.util.Objects;

@Component
@Log4j2
public class KeycloakClient {


    public String getToken( String keycloakUrl, String keycloakRealm, String keycloakClient, String user, String password) {
        RestTemplate restTemplate = new RestTemplate();
        String url = keycloakUrl + "realms/" + keycloakRealm + "/protocol/openid-connect/token";

        log.info("Trying to get token:");
        log.info("keycloakUrl: {}", keycloakUrl);
        log.info("tokenUrl: {}", url);
        log.info("keycloakRealm: {}", keycloakRealm);
        log.info("keycloakClient: {}", keycloakClient);
        log.info("user: {}", user);

        MultiValueMap<String, String> headers = new LinkedMultiValueMap<>();
        headers.add("Content-Type", "application/x-www-form-urlencoded");

        MultiValueMap<String, String> map =
                new LinkedMultiValueMap<>();
        map.add("client_id", keycloakClient);
        map.add("password", password);
        map.add("username", user);
        map.add("grant_type", OAuth2Constants.PASSWORD);

        HttpEntity<MultiValueMap<String, String>> entity = new HttpEntity<>(map, headers);

        ResponseEntity<AccessTokenDTO> responseEntity = restTemplate.exchange(url, HttpMethod.POST, entity, AccessTokenDTO.class);
        AccessTokenDTO accessToken = Objects.requireNonNull(responseEntity.getBody());

        log.info("Token: {}", accessToken.getBearerToken());

        return accessToken.getBearerToken();
    }


}
