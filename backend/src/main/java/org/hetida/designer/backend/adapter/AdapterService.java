package org.hetida.designer.backend.adapter;

import org.hetida.designer.backend.dto.adapter.MetaDataDTO;
import org.springframework.web.client.HttpStatusCodeException;

public interface AdapterService {

    MetaDataDTO getMetaData() throws HttpStatusCodeException;

}
