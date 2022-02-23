package org.hetida.designer.backend.service;


public interface KafkaService {
    void sendMessage(String topic,String key, String body);
}
