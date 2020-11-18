package org.hetida.designer.backend.dto;

import lombok.Data;

@Data
public class AccessTokenDTO {

    private String access_token;
    private Integer expires_in;
    private Integer refresh_expires_in;
    private String refresh_token;
    private String token_type;
    private String session_state;
    private String scope;

    public String getBearerToken(){
        return "Bearer " + access_token;
    }
}
