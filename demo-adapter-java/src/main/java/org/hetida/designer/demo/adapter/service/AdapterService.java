package org.hetida.designer.demo.adapter.service;

import org.hetida.designer.demo.adapter.dto.*;

import java.io.OutputStream;
import java.util.List;

public interface AdapterService {

    AdapterInfoDTO getAdapterInfo();
    SourcesDTO getFilteredSources(final String filter);
    SourceDTO getSource(final String id);
    SinksDTO getFilteredSinks(final String filter);
    SinkDTO getSinkMetaData(final String id);
    ThingNodeDTO getThingNode(final String id);
    StructureDTO getCompleteStructure();
    StructureDTO getStructure(final String parentId);
    List<MetaDataRequestResponseDTO> getSinkMetaData(final String id, String key);
    List<MetaDataRequestResponseDTO> getThingNodeMetadata(final String id, String key);
    void startTimeseriesStreaming(final OutputStream outputStream, final String[] timeseriesIds, final TimeSeriesCriteriaDto timeSeriesCriteriaDto);
    void startDataframeStreaming(final OutputStream outputStream, final String id);
    List<DataFrameDTO> addDataframe(final String id);
    List<MetaDataRequestResponseDTO> getSourceMetaData(final String id, final String key);
}
