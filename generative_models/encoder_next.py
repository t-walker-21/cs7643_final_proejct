"""
Class to define GAN discriminator
"""

import torch
from torchvision import models
import torch.nn as nn
import numpy

class Encoder(nn.Module):
    def __init__(self, cnn_model, input_dim, hidden_dim, lstm_layers, embedding_dim, sequence_len):
        super(Encoder, self).__init__()

        # Convolutions (pre-trained)
        self.cnn_embedding_dim = None

        if (cnn_model == "vgg"):
            self.cnn = models.vgg16(pretrained=True).features
            self.cnn_embedding_dim = 25088

        elif (cnn_model == "resnet"):
            self.cnn = models.resnet(pretrained=True).features
            self.cnn_embedding_dim = 1024

        self.fc1 = nn.Linear(self.cnn_embedding_dim, input_dim)
        self.fc2 = nn.Linear(hidden_dim, embedding_dim)
        self.unpool_1 = nn.Upsample(scale_factor=5, mode='bilinear')
        self.deconv_1 = nn.ConvTranspose2d(in_channels=8, out_channels=3, kernel_size=200, stride=1)

        #Activations
        self.relu = nn.ReLU()
        self.leaky_relu = nn.LeakyReLU(0.2)

        #LSTM
        self.LSTM = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,        
            num_layers=lstm_layers,       
            batch_first=True       # input & output will has batch size as 1s dimension. e.g. (batch, time_step, input_size)
        )

        self.sequence_len = sequence_len

        # Lock conv layers
        #self.cnn.eval()

    def forward(self, x):
        """
        Unroll video tensor and pass through cnn feature extractor
        """

        x = x.view(-1, 3, 224, 224)

        conv_feats = self.cnn(x).view(-1, self.cnn_embedding_dim)
        embedding = self.fc1(conv_feats)
        embedding = self.relu(embedding)

        hidden = None

        # Initialize initial hidden state
        out, hidden = self.LSTM(embedding.view(1, self.sequence_len, -1), hidden)
            
        out = self.fc2(out)
        out = self.relu(out)[:,:,:].view(self.sequence_len, 8 , 5, 5)

        out = self.unpool_1(out)
        out = self.deconv_1(out)

        #print(out.shape)

        return out