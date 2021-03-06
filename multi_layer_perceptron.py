# -*- coding: utf-8 -*-
"""Multi-layer Perceptron.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1e-qlnjnYRFpSj8rhVTpDct1leOINUu6E

## Requirements
"""

import keras                          # Used just for importing MNIST dataset
import numpy as np                    # Used for numerical python
import matplotlib.pyplot as plt       # Used for plotting
from tqdm.notebook import tqdm, trange# Used for showing progress

"""## Classes"""

class Layer:
    def __init__(self, input_units, output_units, learning_rate=0.2):
        self.learning_rate = learning_rate

        self.weights = np.random.normal(
          loc=0.0, 
          scale = np.sqrt(2/(input_units+output_units)), 
          size = (input_units,output_units))
        self.biases = np.zeros(output_units)
        
    def forward(self,input):
        return np.maximum(0, np.dot(input,self.weights) + self.biases)

    def backward(self,input,grad_output):
        relu_grad = input > 0
        grad_input = np.dot(grad_output, self.weights.T)

        grad_weights = np.dot(input.T, grad_output)
        grad_biases = grad_output.mean(axis=0) * input.shape[0]

        self.weights = self.weights - self.learning_rate * grad_weights
        self.biases = self.biases - self.learning_rate * grad_biases
        return grad_input

"""## Functions"""

def softmax_crossentropy_with_logits(logits,reference_answers):
    logits_for_answers = logits[np.arange(len(logits)),reference_answers]
    xentropy = - logits_for_answers + np.log(np.sum(np.exp(logits),axis=-1))
    return xentropy

def grad_softmax_crossentropy_with_logits(logits,reference_answers):
    ones_for_answers = np.zeros_like(logits)
    ones_for_answers[np.arange(len(logits)),reference_answers] = 1
    softmax = np.exp(logits) / np.exp(logits).sum(axis=-1,keepdims=True)
    return (- ones_for_answers + softmax) / logits.shape[0]

def forward(network, X):
    activations = []
    input = X
    for l in network:
        activations.append(l.forward(input))
        input = activations[-1]
    return activations

def forward_with_dropout(network, X, keep_prob):
    activations = []
    input = X
    for l in network:
        D1 = np.random.rand(l.weights.shape[0], l.weights.shape[1])
        D1 = D1 < keep_prob  
        l_drop = l
        l_drop.weights = np.multiply(l.weights, D1)

        activations.append(l_drop.forward(input))
        input = activations[-1]  
          
    return activations

def predict(network,X):
    logits = forward(network,X)[-1]
    return logits.argmax(axis=-1)

def train(network,X,y, reg='none', reg_val=0):
    if reg == 'none':
      layer_activations = forward(network,X)
    elif reg == 'dropout':
      layer_activations = forward_with_dropout(network,X, reg_val)

    layer_inputs = [X] + layer_activations
    logits = layer_activations[-1]

    loss = softmax_crossentropy_with_logits(logits,y)
    loss_grad = grad_softmax_crossentropy_with_logits(logits,y)

    for layer_index in range(len(network))[::-1]:
        layer = network[layer_index]
        loss_grad = layer.backward(layer_inputs[layer_index],loss_grad)
        
    return np.mean(loss)

def salt_pepper(images, amount=0.0005):
  s_vs_p = 0.5
  
  for image in images:
    row,col = image.shape

    num_salt = np.ceil(amount * image.size * s_vs_p)
    coords = [np.random.randint(0, i - 1, int(num_salt))
            for i in image.shape]
    image[coords] = 1

    num_pepper = np.ceil(amount* image.size * (1. - s_vs_p))
    coords = [np.random.randint(0, i - 1, int(num_pepper))
            for i in image.shape]
    image[coords] = 0

  return images

"""## Experiment Params"""

max_epoch = 25
max_epoch_es = 50

# Model param selections
max_hidden_layers = 5
node_counts = [32, 64, 128, 200, 256]
base_node_count = 64

# Model params
best_layer_count = -1
best_node_count = -1
best_layer_count_es = -1
best_node_count_es = -1

# testing params
keep_levels = [1, 0.99995, 0.9995, 0.995, 0.95]
sp_levels = [0, 0.005, 0.05, 0.5]

"""## MLP Experimentation
Testing hidden layer and hidden layer node count
"""

# Get data
(X_train, y_train), (X_test, y_test) = keras.datasets.mnist.load_data()

# Separate training and validation data
X_train = X_train.astype(float) / 255.
X_test = X_test.astype(float) / 255.
X_train, X_val = X_train[:-10000], X_train[-10000:]
y_train, y_val = y_train[:-10000], y_train[-10000:]
    
# Flattening image    
X_train = X_train.reshape([X_train.shape[0], -1])
X_val = X_val.reshape([X_val.shape[0], -1])
X_test = X_test.reshape([X_test.shape[0], -1])

print('Testing various numbers of hidden layers')
test_log = []
val_log = []
for num_layers in trange(0, max_hidden_layers):
  print('# layer: ', num_layers)

  # Create Base MLP
  network = []
  network.append(Layer(X_train.shape[1],100))
  network.append(Layer(100,base_node_count))

  for i in range(num_layers):
    network.append(Layer(base_node_count,base_node_count))

  # Output layer
  network.append(Layer(base_node_count,10))

  print("Training network on " + str(max_epoch) + " epochs")
  for epoch in trange(max_epoch):
    train(network, X_train, y_train)

  # Make predictions
  val_acc = np.mean(predict(network,X_val)==y_val)
  test_acc = np.mean(predict(network,X_test)==y_test)

  # Assessing best test results
  if len(test_log) < 1:
    best_layer_count = num_layers
  elif max(test_log) < test_acc:
    best_layer_count = num_layers

  test_log.append(test_acc)
  val_log.append(val_acc)

plt.plot(range(1, max_hidden_layers + 1), test_log, label='Test acc.')
plt.plot(range(1, max_hidden_layers + 1), val_log, label='Val acc.')
plt.ylabel('Accuracy')
plt.xlabel('# Hidden Layers')
plt.legend(loc='best')
plt.grid()
plt.show()

print('///// Results /////')
print('Best # layers: ' + str(best_layer_count + 1))
print('Test acc: ' + str(test_log[best_layer_count]))
print('Val acc: ' + str(val_log[best_layer_count]))

#########

print('Testing various node counts for ' + str(best_layer_count + 1) + ' hidden layers')
# Logging data
val_log = []
test_log = []
for num_nodes in tqdm(node_counts):
  print('hidden layer nodes: ', num_nodes)

  # Create Base MLP
  network = []
  network.append(Layer(X_train.shape[1],100))
  network.append(Layer(100,num_nodes))

  for i in range(best_layer_count):
    network.append(Layer(num_nodes,num_nodes))

  # Output layer
  network.append(Layer(num_nodes,10))

  print("Training network on " + str(max_epoch) + " epochs")
  for epoch in trange(max_epoch):
    train(network, X_train, y_train)
    
  # Make predictions
  test_acc = np.mean(predict(network,X_test)==y_test)
  val_acc = np.mean(predict(network,X_val)==y_val)

  if len(test_log) < 1:
    best_node_count = num_nodes
  elif max(test_log) < test_acc:
    best_node_count = num_nodes

  test_log.append(test_acc)
  val_log.append(val_acc)

plt.plot(node_counts, test_log,label='Test acc.')
plt.plot(node_counts, val_log,label='Val acc.')
plt.ylabel('Accuracy')
plt.xlabel('# Nodes per Hidden Layer')
plt.legend(loc='best')
plt.grid()
plt.show()

print('///// Results /////')
print('Best # nodes: ' + str(best_node_count))
print('Test acc: ' + str(test_log[node_counts.index(best_node_count)]))
print('Val acc: ' + str(val_log[node_counts.index(best_node_count)]))

"""## Early stopping"""

# Get data
(X_train, y_train), (X_test, y_test) = keras.datasets.mnist.load_data()

# Separate training and validation data
X_train = X_train.astype(float) / 255.
X_test = X_test.astype(float) / 255.
X_train, X_val = X_train[:-10000], X_train[-10000:]
y_train, y_val = y_train[:-10000], y_train[-10000:]
    
# Flattening image    
X_train = X_train.reshape([X_train.shape[0], -1])
X_val = X_val.reshape([X_val.shape[0], -1])
X_test = X_test.reshape([X_test.shape[0], -1])

print('Testing various numbers of hidden layers')
test_log = []
val_log = []
for num_layers in trange(0, max_hidden_layers):
  print('# layer: ', num_layers)

  # Create Base MLP
  network = []
  network.append(Layer(X_train.shape[1],100))
  network.append(Layer(100,base_node_count))

  for i in range(num_layers):
    network.append(Layer(base_node_count,base_node_count))

  # Output layer
  network.append(Layer(base_node_count,10))

  print("Training network on " + str(max_epoch_es) + " epochs")
  last_loss = -100
  for epoch in trange(max_epoch_es):
    mean_loss = train(network, X_train, y_train)

    if last_loss == -100:
      last_loss = mean_loss
    elif mean_loss > last_loss:
      print('Stopping early on epoch: ', epoch)
      break
    else:
      last_loss = mean_loss

  # Make predictions
  val_acc = np.mean(predict(network,X_val)==y_val)
  test_acc = np.mean(predict(network,X_test)==y_test)

  # Assessing best test results
  if len(test_log) < 1:
    best_layer_count_es = num_layers
  elif max(test_log) < test_acc:
    best_layer_count_es = num_layers

  test_log.append(test_acc)
  val_log.append(val_acc)

plt.plot(range(1, max_hidden_layers + 1), test_log, label='Test acc.')
plt.plot(range(1, max_hidden_layers + 1), val_log, label='Val acc.')
plt.ylabel('Accuracy')
plt.xlabel('# Hidden Layers')
plt.legend(loc='best')
plt.grid()
plt.show()

print('///// Results /////')
print('Best # layers: ' + str(best_layer_count_es + 1))
print('Test acc: ' + str(test_log[best_layer_count_es]))
print('Val acc: ' + str(val_log[best_layer_count_es]))


#########

print('Testing various node counts for ' + str(best_layer_count_es + 1) + ' hidden layers')
val_log = []
test_log = []
for num_nodes in tqdm(node_counts):
  print('hidden layer nodes: ', num_nodes)

  # Create Base MLP
  network = []
  network.append(Layer(X_train.shape[1],100))
  network.append(Layer(100,num_nodes))

  for i in range(best_layer_count_es):
    network.append(Layer(num_nodes,num_nodes))

  # Output layer
  network.append(Layer(num_nodes,10))

  print("Training network on " + str(max_epoch_es) + " epochs")
  last_acc = -100
  for epoch in trange(max_epoch_es):
    mean_loss = train(network, X_train, y_train)
    mean_acc = np.mean(predict(network,X_test)==y_test)

    if last_acc == -100:
      last_acc = mean_acc
    elif mean_acc < last_acc:
      print('Stopping early on epoch: ', epoch)
      break
    else:
      last_acc = mean_acc
    
  # Make predictions
  test_acc = np.mean(predict(network,X_test)==y_test)
  val_acc = np.mean(predict(network,X_val)==y_val)

  if len(test_log) < 1:
    best_node_count_es = num_nodes
  elif max(test_log) < test_acc:
    best_node_count_es = num_nodes

  test_log.append(test_acc)
  val_log.append(val_acc)

plt.plot(node_counts, test_log,label='Test acc.')
plt.plot(node_counts, val_log,label='Val acc.')
plt.ylabel('Accuracy')
plt.xlabel('# Nodes per Hidden Layer')
plt.legend(loc='best')
plt.grid()
plt.show()

print('///// Results /////')
print('Best # nodes: ' + str(best_node_count_es))
print('Test acc: ' + str(test_log[node_counts.index(best_node_count_es)]))
print('Val acc: ' + str(val_log[node_counts.index(best_node_count_es)]))

"""## Dropout"""

print('Testing various levels of dropout on model')
print("Hidden layers: " + str(best_layer_count + 1))
print("Hidden layer nodes: " + str(best_node_count))
final_results = []
for keep_level in tqdm(keep_levels):
  print('Keep level: ' + str(keep_level))

  # Training network
  network = []
  network.append(Layer(X_train.shape[1],100))
  network.append(Layer(100,best_node_count))

  for i in range(best_layer_count):
    network.append(Layer(best_node_count,best_node_count))

  # Output layer
  network.append(Layer(best_node_count,10))

  # Logging data
  test_log = []

  print("Training network on " + str(max_epoch) + " epochs")
  for epoch in trange(max_epoch):
    if keep_level >= 1:    
      train(network, X_train, y_train)
    else:
      train(network, X_train, y_train, 'dropout', keep_level)

    # Make predictions
    test_log.append(np.mean(predict(network,X_test)==y_test))

  final_results.append(test_log[-1])
  title = 'Keep level ' + str(keep_level)
  plt.plot(test_log,label=title)
plt.legend(loc='best')
plt.ylabel('Accuracy')
plt.xlabel('Epochs')
plt.grid()
plt.show()

print('///// Results /////')
for i in range(0, len(keep_levels)):
  print('Keep lvl. ' + str(keep_levels[i]) + ' Test acc. ' + str(final_results[i]))

"""## Dropout w/ Early Stopping"""

print('Testing various levels of dropout on model')
print("Hidden layers: " + str(best_layer_count_es + 1))
print("Hidden layer nodes: " + str(best_node_count_es))
final_results = []
for keep_level in tqdm(keep_levels):
  print('Keep level: ' + str(keep_level))

  # Training network
  network = []
  network.append(Layer(X_train.shape[1],100))
  network.append(Layer(100,best_node_count_es))

  for i in range(best_layer_count_es):
    network.append(Layer(best_node_count_es,best_node_count_es))

  # Output layer
  network.append(Layer(best_node_count_es,10))

  # Logging data
  test_log = []

  print("Training network on " + str(max_epoch_es) + " epochs")
  last_acc = -100
  for epoch in trange(max_epoch_es):
    if keep_level >= 1:    
      train(network, X_train, y_train)
    else:
      train(network, X_train, y_train, 'dropout', keep_level)

    mean_acc = np.mean(predict(network,X_test)==y_test)
    if last_acc == -100:
      last_acc = mean_acc
    elif mean_acc < last_acc:
      print('Stopping early on epoch: ', epoch)
      break
    else:
      last_acc = mean_acc

    # Make predictions
    test_log.append(np.mean(predict(network,X_test)==y_test))

  final_results.append(test_log[-1])
  title = 'Keep level ' + str(keep_level)
  plt.plot(test_log,label=title)
plt.legend(loc='best')
plt.ylabel('Accuracy')
plt.xlabel('Epochs')
plt.grid()
plt.show()

print('///// Results /////')
for i in range(0, len(keep_levels)):
  print('Keep lvl. ' + str(keep_levels[i]) + ' Test acc. ' + str(final_results[i]))

"""## Noise
Salt and pepper
"""

# Getting / preparing data
(X_train_orig, y_train), (X_test_orig, y_test) = keras.datasets.mnist.load_data()
X_train_orig = X_train_orig.astype(float) / 255.
X_test_orig = X_test_orig.astype(float) / 255.
X_train_orig, X_val_orig = X_train_orig[:-10000], X_train_orig[-10000:]
y_train, y_val = y_train[:-10000], y_train[-10000:]

print('Testing various levels of noise on model')
print("Hidden layers: " + str(best_layer_count + 1))
print("Hidden layer nodes: " + str(best_node_count))
final_results = []
for sp_level in tqdm(sp_levels):
  print('Noise level: ' + str(sp_level))

  X_train = X_train_orig
  X_val = X_val_orig
  X_test = X_test_orig

  if sp_level > 0:    
    X_train = salt_pepper(X_train, sp_level)
    X_val = salt_pepper(X_val, sp_level)
    X_test = salt_pepper(X_test, sp_level)

  X_train = X_train.reshape([X_train.shape[0], -1])
  X_val = X_val.reshape([X_val.shape[0], -1])
  X_test = X_test.reshape([X_test.shape[0], -1])

  # Training network
  network = []
  network.append(Layer(X_train.shape[1],100))
  network.append(Layer(100,best_node_count))

  for i in range(best_layer_count):
    network.append(Layer(best_node_count,best_node_count))

  # Output layer
  network.append(Layer(best_node_count,10))

  # Logging data
  test_log = []

  print("Training network on " + str(max_epoch) + " epochs")
  for epoch in trange(max_epoch):
    train(network, X_train, y_train)
    
    # Make predictions
    test_log.append(np.mean(predict(network,X_test)==y_test))

  final_results.append(test_log[-1])
  title = 'Noise level ' + str(sp_level)
  plt.plot(test_log,label=title)
plt.legend(loc='best')
plt.ylabel('Accuracy')
plt.xlabel('Epochs')
plt.grid()
plt.show()

print('///// Results /////')
for i in range(0, len(sp_levels)):
  print('Noise lvl. ' + str(sp_levels[i]) + ' Test acc. ' + str(final_results[i]))

"""## Noise w/ Early Stopping"""

# Getting / preparing data
(X_train_orig, y_train), (X_test_orig, y_test) = keras.datasets.mnist.load_data()
X_train_orig = X_train_orig.astype(float) / 255.
X_test_orig = X_test_orig.astype(float) / 255.
X_train_orig, X_val_orig = X_train_orig[:-10000], X_train_orig[-10000:]
y_train, y_val = y_train[:-10000], y_train[-10000:]

print('Testing various levels of noise on model')
print("Hidden layers: " + str(best_layer_count_es + 1))
print("Hidden layer nodes: " + str(best_node_count_es))

final_results = []
for sp_level in tqdm(sp_levels):
  print('Noise level: ' + str(sp_level))
  X_train = X_train_orig
  X_val = X_val_orig
  X_test = X_test_orig

  if sp_level > 0:    
    X_train = salt_pepper(X_train, sp_level)
    X_val = salt_pepper(X_val, sp_level)
    X_test = salt_pepper(X_test, sp_level)

  X_train = X_train.reshape([X_train.shape[0], -1])
  X_val = X_val.reshape([X_val.shape[0], -1])
  X_test = X_test.reshape([X_test.shape[0], -1])

  # Training network
  network = []
  network.append(Layer(X_train.shape[1],100))
  network.append(Layer(100,best_node_count_es))

  for i in range(best_layer_count_es):
    network.append(Layer(best_node_count_es,best_node_count_es))

  # Output layer
  network.append(Layer(best_node_count_es,10))

  # Logging data
  test_log = []

  print("Training network on " + str(max_epoch_es) + " epochs")
  last_acc = -100
  for epoch in trange(max_epoch_es):
    train(network, X_train, y_train)
    mean_acc = np.mean(predict(network,X_test)==y_test)

    if last_acc == -100:
      last_acc = mean_acc
    elif mean_acc < last_acc:
      print('Stopping early on epoch: ', epoch)
      break
    else:
      last_acc = mean_acc
    
    # Make predictions
    test_log.append(np.mean(predict(network,X_test)==y_test))

  final_results.append(test_log[-1])
  title = 'Noise level ' + str(sp_level)
  plt.plot(test_log,label=title)
plt.legend(loc='best')
plt.ylabel('Accuracy')
plt.xlabel('Epochs')
plt.grid()
plt.show()

print('///// Results /////')
for i in range(0, len(sp_levels)):
  print('Noise lvl. ' + str(sp_levels[i]) + ' Test acc. ' + str(final_results[i]))