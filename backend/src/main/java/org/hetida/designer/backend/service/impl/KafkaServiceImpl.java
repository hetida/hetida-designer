package org.hetida.designer.backend.service.impl;

import lombok.extern.log4j.Log4j2;
import org.hetida.designer.backend.service.KafkaService;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.support.SendResult;
import org.springframework.stereotype.Service;
import org.springframework.util.concurrent.ListenableFuture;
import org.springframework.util.concurrent.ListenableFutureCallback;

import javax.annotation.Resource;

@Service
@Log4j2
public class KafkaServiceImpl implements KafkaService {

    @Resource
    KafkaTemplate<String,String> kafkaTemplate;


    @Override
    public void sendMessage(String topic, String key, String body) {
        Runnable runnable =
                () -> {
                    ListenableFuture<SendResult<String, String>> future = kafkaTemplate.send(topic, key, body);
                    future.addCallback(new ListenableFutureCallback<SendResult<String, String>>() {

                        @Override
                        public void onSuccess(SendResult<String, String> result) {
                            log.info("message to " + topic + " successfully send");
                        }

                        @Override
                        public void onFailure(Throwable ex) {
                            log.error("message to " + topic + " NOT send. Cause: " + ex.getMessage(), ex);
                        }
                    });
                };
        Thread thread = new Thread(runnable);
        thread.start();
    }
}
