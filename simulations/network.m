

clear; clc;


inputSize = 1; 


numSamples = 1000;
X_dummy = rand(numSamples, inputSize);
Y_dummy = X_dummy; 


layers = [
    featureInputLayer(inputSize, 'Normalization', 'none', 'Name', 'input')
    fullyConnectedLayer(inputSize, 'Name', 'pass_through')
    regressionLayer('Name', 'output')
];


options = trainingOptions('adam', ...
    'MaxEpochs', 15, ...      
    'InitialLearnRate', 0.1, ... 
    'Verbose', false, ...
    'Plots', 'none');


disp('Compiling pass-through network...');
net = trainNetwork(X_dummy, Y_dummy, layers, options);


save('network.mat', 'net');
disp('Success! network.mat has been saved to your current folder.');