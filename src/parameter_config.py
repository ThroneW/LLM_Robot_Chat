# -*- coding: utf-8 -*-
import torch


class ParameterConfig():
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.vocab_path = '../vocab/vocab.txt'
        self.train_path = './data/medical_train.pkl'
        self.valid_path = './data/medical_valid.pkl'
        self.config_json = './config/config.json'
        self.save_model_path = 'save_model1'
        self.pretrained_model = ''
        self.save_samples_path = 'sample'
        self.ignore_index = -100
        self.max_history_len = 3
        self.max_len = 300  #
        self.repetition_penalty = 10.0
        self.topk = 4
        self.batch_size = 16
        self.epochs = 150
        self.loss_step = 100
        self.lr = 2.6e-5
        self.eps = 1.0e-09
        self.max_grad_norm = 2.0
        self.gradient_accumulation_steps = 4
        self.warmup_steps = 100

