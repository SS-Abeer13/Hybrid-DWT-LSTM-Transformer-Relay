classdef Squeeze_To_UnsqueezeLayer1030 < nnet.layer.Layer & nnet.layer.Formattable
    % A custom layer auto-generated while importing an ONNX network.
    
    %#codegen
    %#ok<*PROPLC>
    %#ok<*NBRAK>
    %#ok<*INUSL>
    %#ok<*VARARG>
    
    properties (Learnable)
        model_classifier_0_b
        model_classifier_0_w
        model_classifier_3_b
        model_classifier_3_w
        onnx__MatMul_405
        onnx__ReduceSum_323
        x_Constant_output_0
        x_model_Constant_out
        x_model_layer_norm_4
        x_model_lstm_Cons_11
    end
    
    properties
        ONNXParams         % An ONNXParameters object containing parameters used by this layer.
    end
    
    methods
        function this = Squeeze_To_UnsqueezeLayer1030(name, onnxParams)
            this.Name = name;
            this.OutputNames = {'probability'};
            this.ONNXParams = onnxParams;
            this.model_classifier_0_b = onnxParams.Learnables.model_classifier_0_b;
            this.model_classifier_0_w = onnxParams.Learnables.model_classifier_0_w;
            this.model_classifier_3_b = onnxParams.Learnables.model_classifier_3_b;
            this.model_classifier_3_w = onnxParams.Learnables.model_classifier_3_w;
            this.onnx__MatMul_405 = onnxParams.Learnables.onnx__MatMul_405;
            this.onnx__ReduceSum_323 = onnxParams.Learnables.onnx__ReduceSum_323;
            this.x_Constant_output_0 = onnxParams.Learnables.x_Constant_output_0;
            this.x_model_Constant_out = onnxParams.Learnables.x_model_Constant_out;
            this.x_model_layer_norm_4 = onnxParams.Learnables.x_model_layer_norm_4;
            this.x_model_lstm_Cons_11 = onnxParams.Learnables.x_model_lstm_Cons_11;
        end
        
        function [probability] = predict(this, x_model_lstm_LSTM_2_)
            if isdlarray(x_model_lstm_LSTM_2_)
                x_model_lstm_LSTM_2_ = stripdims(x_model_lstm_LSTM_2_);
            end
            x_model_lstm_LSTM_2_NumDims = 4;
            onnxParams = this.ONNXParams;
            onnxParams.Learnables.model_classifier_0_b = this.model_classifier_0_b;
            onnxParams.Learnables.model_classifier_0_w = this.model_classifier_0_w;
            onnxParams.Learnables.model_classifier_3_b = this.model_classifier_3_b;
            onnxParams.Learnables.model_classifier_3_w = this.model_classifier_3_w;
            onnxParams.Learnables.onnx__MatMul_405 = this.onnx__MatMul_405;
            onnxParams.Learnables.onnx__ReduceSum_323 = this.onnx__ReduceSum_323;
            onnxParams.Learnables.x_Constant_output_0 = this.x_Constant_output_0;
            onnxParams.Learnables.x_model_Constant_out = this.x_model_Constant_out;
            onnxParams.Learnables.x_model_layer_norm_4 = this.x_model_layer_norm_4;
            onnxParams.Learnables.x_model_lstm_Cons_11 = this.x_model_lstm_Cons_11;
            [probability, probabilityNumDims] = Squeeze_To_UnsqueezeFcn(x_model_lstm_LSTM_2_, x_model_lstm_LSTM_2_NumDims, onnxParams, 'Training', false, ...
                'InputDataPermutation', {[3 4 2 1], ['as-is']}, ...
                'OutputDataPermutation', {['as-is'], ['as-is']});
            if any(cellfun(@(A)~isnumeric(A), {probability}))
                fprintf('Runtime error in network. The custom layer ''%s'' output a non-numeric value.\n', 'Squeeze_To_UnsqueezeLayer1030');
                error(message('nnet_cnn_onnx:onnx:BadCustomLayerRuntimeOutput', 'Squeeze_To_UnsqueezeLayer1030'));
            end
            probability = dlarray(single(probability), repmat('U', 1, max(2, probabilityNumDims)));
            if ~coder.target('MATLAB')
                probability = extractdata(probability);
            end
        end
        
        function [probability] = forward(this, x_model_lstm_LSTM_2_)
            if isdlarray(x_model_lstm_LSTM_2_)
                x_model_lstm_LSTM_2_ = stripdims(x_model_lstm_LSTM_2_);
            end
            x_model_lstm_LSTM_2_NumDims = 4;
            onnxParams = this.ONNXParams;
            onnxParams.Learnables.model_classifier_0_b = this.model_classifier_0_b;
            onnxParams.Learnables.model_classifier_0_w = this.model_classifier_0_w;
            onnxParams.Learnables.model_classifier_3_b = this.model_classifier_3_b;
            onnxParams.Learnables.model_classifier_3_w = this.model_classifier_3_w;
            onnxParams.Learnables.onnx__MatMul_405 = this.onnx__MatMul_405;
            onnxParams.Learnables.onnx__ReduceSum_323 = this.onnx__ReduceSum_323;
            onnxParams.Learnables.x_Constant_output_0 = this.x_Constant_output_0;
            onnxParams.Learnables.x_model_Constant_out = this.x_model_Constant_out;
            onnxParams.Learnables.x_model_layer_norm_4 = this.x_model_layer_norm_4;
            onnxParams.Learnables.x_model_lstm_Cons_11 = this.x_model_lstm_Cons_11;
            [probability, probabilityNumDims] = Squeeze_To_UnsqueezeFcn(x_model_lstm_LSTM_2_, x_model_lstm_LSTM_2_NumDims, onnxParams, 'Training', true, ...
                'InputDataPermutation', {[3 4 2 1], ['as-is']}, ...
                'OutputDataPermutation', {['as-is'], ['as-is']});
            if any(cellfun(@(A)~isnumeric(A), {probability}))
                fprintf('Runtime error in network. The custom layer ''%s'' output a non-numeric value.\n', 'Squeeze_To_UnsqueezeLayer1030');
                error(message('nnet_cnn_onnx:onnx:BadCustomLayerRuntimeOutput', 'Squeeze_To_UnsqueezeLayer1030'));
            end
            probability = dlarray(single(probability), repmat('U', 1, max(2, probabilityNumDims)));
            if ~coder.target('MATLAB')
                probability = extractdata(probability);
            end
        end
    end
end

function [probability, probabilityNumDims, state] = Squeeze_To_UnsqueezeFcn(x_model_lstm_LSTM_2_, x_model_lstm_LSTM_2_NumDims, params, varargin)
%SQUEEZE_TO_UNSQUEEZEFCN Function implementing an imported ONNX network.
%
% THIS FILE WAS AUTO-GENERATED BY importONNXFunction.
% ONNX Operator Set Version: 14
%
% Variable names in this function are taken from the original ONNX file.
%
% [PROBABILITY] = Squeeze_To_UnsqueezeFcn(X_MODEL_LSTM_LSTM_2_, PARAMS)
%			- Evaluates the imported ONNX network SQUEEZE_TO_UNSQUEEZEFCN with input(s)
%			X_MODEL_LSTM_LSTM_2_ and the imported network parameters in PARAMS. Returns
%			network output(s) in PROBABILITY.
%
% [PROBABILITY, STATE] = Squeeze_To_UnsqueezeFcn(X_MODEL_LSTM_LSTM_2_, PARAMS)
%			- Additionally returns state variables in STATE. When training,
%			use this form and set TRAINING to true.
%
% [__] = Squeeze_To_UnsqueezeFcn(X_MODEL_LSTM_LSTM_2_, PARAMS, 'NAME1', VAL1, 'NAME2', VAL2, ...)
%			- Specifies additional name-value pairs described below:
%
% 'Training'
% 			Boolean indicating whether the network is being evaluated for
%			prediction or training. If TRAINING is true, state variables
%			will be updated.
%
% 'InputDataPermutation'
%			'auto' - Automatically attempt to determine the permutation
%			 between the dimensions of the input data and the dimensions of
%			the ONNX model input. For example, the permutation from HWCN
%			(MATLAB standard) to NCHW (ONNX standard) uses the vector
%			[4 3 1 2]. See the documentation for IMPORTONNXFUNCTION for
%			more information about automatic permutation.
%
%			'none' - Input(s) are passed in the ONNX model format. See 'Inputs'.
%
%			numeric vector - The permutation vector describing the
%			transformation between input data dimensions and the expected
%			ONNX input dimensions.%
%			cell array - If the network has multiple inputs, each cell
%			contains 'auto', 'none', or a numeric vector.
%
% 'OutputDataPermutation'
%			'auto' - Automatically attempt to determine the permutation
%			between the dimensions of the output and a conventional MATLAB
%			dimension ordering. For example, the permutation from NC (ONNX
%			standard) to CN (MATLAB standard) uses the vector [2 1]. See
%			the documentation for IMPORTONNXFUNCTION for more information
%			about automatic permutation.
%
%			'none' - Return output(s) as given by the ONNX model. See 'Outputs'.
%
%			numeric vector - The permutation vector describing the
%			transformation between the ONNX output dimensions and the
%			desired output dimensions.%
%			cell array - If the network has multiple outputs, each cell
%			contains 'auto', 'none' or a numeric vector.
%
% Inputs:
% -------
% X_MODEL_LSTM_LSTM_2_
%			- Input(s) to the ONNX network.
%			  The input size(s) expected by the ONNX file are:
%				  X_MODEL_LSTM_LSTM_2_:		[Unknown, Unknown, Unknown, Unknown]				Type: FLOAT
%			  By default, the function will try to permute the input(s)
%			  into this dimension ordering. If the default is incorrect,
%			  use the 'InputDataPermutation' argument to control the
%			  permutation.
%
%
% PARAMS	- Network parameters returned by 'importONNXFunction'.
%
%
% Outputs:
% --------
% PROBABILITY
%			- Output(s) of the ONNX network.
%			  Without permutation, the size(s) of the outputs are:
%				  PROBABILITY:		[1, 1]				Type: FLOAT
%			  By default, the function will try to permute the output(s)
%			  from this dimension ordering into a conventional MATLAB
%			  ordering. If the default is incorrect, use the
%			  'OutputDataPermutation' argument to control the permutation.
%
% STATE		- (Optional) State variables. When TRAINING is true, these will
% 			  have been updated from the original values in PARAMS.State.
%
%
%  See also importONNXFunction

% Preprocess the input data and arguments:
[x_model_lstm_LSTM_2_, Training, outputDataPerms, anyDlarrayInputs] = preprocessInput(x_model_lstm_LSTM_2_, params, varargin{:});
% Put all variables into a single struct to implement dynamic scoping:
[Vars, NumDims] = packageVariables(params, {'x_model_lstm_LSTM_2_'}, {x_model_lstm_LSTM_2_}, [x_model_lstm_LSTM_2_NumDims]);
% Call the top-level graph function:
[probability, probabilityNumDims, state] = Squeeze_To_UnsqueezeGraph1020(x_model_lstm_LSTM_2_, NumDims.x_model_lstm_LSTM_2_, Vars, NumDims, Training, params.State);
% Postprocess the output data
[probability] = postprocessOutput(probability, outputDataPerms, anyDlarrayInputs, Training, varargin{:});
end

function [probability, probabilityNumDims1029, state] = Squeeze_To_UnsqueezeGraph1020(x_model_lstm_LSTM_2_, x_model_lstm_LSTM_2_NumDims1028, Vars, NumDims, Training, state)
% Function implementing the graph 'Squeeze_To_UnsqueezeGraph1020'
% Update Vars and NumDims from the graph's formal input parameters. Note that state variables are already in Vars.
Vars.x_model_lstm_LSTM_2_ = x_model_lstm_LSTM_2_;
NumDims.x_model_lstm_LSTM_2_ = x_model_lstm_LSTM_2_NumDims1028;

% Execute the operators:
% Squeeze:
[Vars.x_model_lstm_Squee_1, NumDims.x_model_lstm_Squee_1] = onnxSqueeze(Vars.x_model_lstm_LSTM_2_, Vars.x_model_lstm_Cons_11, NumDims.x_model_lstm_LSTM_2_);

% Transpose:
[perm, NumDims.x_model_lstm_Transpo] = prepareTransposeArgs(Vars.TransposePerm1021, NumDims.x_model_lstm_Squee_1);
if ~isempty(perm)
    Vars.x_model_lstm_Transpo = permute(Vars.x_model_lstm_Squee_1, perm);
end

% ReduceMean:
dims = prepareReduceArgs(Vars.ReduceMeanAxes1022, NumDims.x_model_lstm_Transpo);
Vars.x_model_layer_nor_1 = mean(Vars.x_model_lstm_Transpo, dims);
NumDims.x_model_layer_nor_1 = NumDims.x_model_lstm_Transpo;

% Sub:
Vars.x_model_layer_nor_4 = Vars.x_model_lstm_Transpo - Vars.x_model_layer_nor_1;
NumDims.x_model_layer_nor_4 = max(NumDims.x_model_lstm_Transpo, NumDims.x_model_layer_nor_1);

% Pow:
Vars.x_model_layer_norm_P = power(Vars.x_model_layer_nor_4, Vars.x_model_layer_norm_4);
NumDims.x_model_layer_norm_P = max(NumDims.x_model_layer_nor_4, NumDims.x_model_layer_norm_4);

% ReduceMean:
dims = prepareReduceArgs(Vars.ReduceMeanAxes1023, NumDims.x_model_layer_norm_P);
Vars.x_model_layer_norm_R = mean(Vars.x_model_layer_norm_P, dims);
NumDims.x_model_layer_norm_R = NumDims.x_model_layer_norm_P;

% Add:
Vars.x_model_layer_norm_1 = Vars.x_model_layer_norm_R + Vars.x_model_layer_norm_C;
NumDims.x_model_layer_norm_1 = max(NumDims.x_model_layer_norm_R, NumDims.x_model_layer_norm_C);

% Sqrt:
Vars.x_model_layer_norm_S = sqrt(Vars.x_model_layer_norm_1);
NumDims.x_model_layer_norm_S = NumDims.x_model_layer_norm_1;

% Div:
Vars.x_model_layer_norm_D = Vars.x_model_layer_nor_4 ./ Vars.x_model_layer_norm_S;
NumDims.x_model_layer_norm_D = max(NumDims.x_model_layer_nor_4, NumDims.x_model_layer_norm_S);

% Mul:
Vars.x_model_layer_norm_M = Vars.x_model_layer_norm_D .* Vars.model_layer_norm_wei;
NumDims.x_model_layer_norm_M = max(NumDims.x_model_layer_norm_D, NumDims.model_layer_norm_wei);

% Add:
Vars.x_model_layer_norm_A = Vars.x_model_layer_norm_M + Vars.model_layer_norm_bia;
NumDims.x_model_layer_norm_A = max(NumDims.x_model_layer_norm_M, NumDims.model_layer_norm_bia);

% MatMul:
[Vars.x_model_attention_Ma, NumDims.x_model_attention_Ma] = onnxMatMul(Vars.x_model_layer_norm_A, Vars.onnx__MatMul_405, NumDims.x_model_layer_norm_A, NumDims.onnx__MatMul_405);

% Add:
Vars.x_model_attention_Ad = Vars.model_attention_bias + Vars.x_model_attention_Ma;
NumDims.x_model_attention_Ad = max(NumDims.model_attention_bias, NumDims.x_model_attention_Ma);

% Softmax:
[Vars.x_model_Softmax_outp, NumDims.x_model_Softmax_outp] = onnxSoftmax13(Vars.x_model_attention_Ad, 1, NumDims.x_model_attention_Ad);

% Mul:
Vars.x_model_Mul_output_0 = Vars.x_model_Softmax_outp .* Vars.x_model_layer_norm_A;
NumDims.x_model_Mul_output_0 = max(NumDims.x_model_Softmax_outp, NumDims.x_model_layer_norm_A);

% ReduceSum:
dims = prepareReduceArgs(Vars.onnx__ReduceSum_323, NumDims.x_model_Mul_output_0);
Vars.x_model_ReduceSum_ou = sum(Vars.x_model_Mul_output_0, dims);
[Vars.x_model_ReduceSum_ou, NumDims.x_model_ReduceSum_ou] = onnxSqueeze(Vars.x_model_ReduceSum_ou, Vars.onnx__ReduceSum_323, NumDims.x_model_Mul_output_0);

% Gemm:
[A, B, C, alpha, beta, NumDims.x_model_classifier_c] = prepareGemmArgs(Vars.x_model_ReduceSum_ou, Vars.model_classifier_0_w, Vars.model_classifier_0_b, Vars.Gemmalpha1024, Vars.Gemmbeta1025, 0, 1, NumDims.model_classifier_0_b);
Vars.x_model_classifier_c = alpha*B*A + beta*C;

% Relu:
Vars.x_model_classifier_1 = relu(Vars.x_model_classifier_c);
NumDims.x_model_classifier_1 = NumDims.x_model_classifier_c;

% Gemm:
[A, B, C, alpha, beta, NumDims.x_model_classifier_2] = prepareGemmArgs(Vars.x_model_classifier_1, Vars.model_classifier_3_w, Vars.model_classifier_3_b, Vars.Gemmalpha1026, Vars.Gemmbeta1027, 0, 1, NumDims.model_classifier_3_b);
Vars.x_model_classifier_2 = alpha*B*A + beta*C;

% Squeeze:
[Vars.x_model_Squeeze_outp, NumDims.x_model_Squeeze_outp] = onnxSqueeze(Vars.x_model_classifier_2, Vars.x_model_Constant_out, NumDims.x_model_classifier_2);

% Sigmoid:
Vars.x_Sigmoid_output_0 = sigmoid(Vars.x_model_Squeeze_outp);
NumDims.x_Sigmoid_output_0 = NumDims.x_model_Squeeze_outp;

% Unsqueeze:
[shape, NumDims.probability] = prepareUnsqueezeArgs(Vars.x_Sigmoid_output_0, Vars.x_Constant_output_0, NumDims.x_Sigmoid_output_0);
Vars.probability = reshape(Vars.x_Sigmoid_output_0, shape);

% Set graph output arguments from Vars and NumDims:
probability = Vars.probability;
probabilityNumDims1029 = NumDims.probability;
% Set output state from Vars:
state = updateStruct(state, Vars);
end

function [inputDataPerms, outputDataPerms, Training] = parseInputs(x_model_lstm_LSTM_2_, numDataOutputs, params, varargin)
% Function to validate inputs to Squeeze_To_UnsqueezeFcn:
p = inputParser;
isValidArrayInput = @(x)isnumeric(x) || isstring(x);
isValidONNXParameters = @(x)isa(x, 'ONNXParameters');
addRequired(p, 'x_model_lstm_LSTM_2_', isValidArrayInput);
addRequired(p, 'params', isValidONNXParameters);
addParameter(p, 'InputDataPermutation', 'auto');
addParameter(p, 'OutputDataPermutation', 'auto');
addParameter(p, 'Training', false);
parse(p, x_model_lstm_LSTM_2_, params, varargin{:});
inputDataPerms = p.Results.InputDataPermutation;
outputDataPerms = p.Results.OutputDataPermutation;
Training = p.Results.Training;
if isnumeric(inputDataPerms)
    inputDataPerms = {inputDataPerms};
end
if isstring(inputDataPerms) && isscalar(inputDataPerms) || ischar(inputDataPerms)
    inputDataPerms = repmat({inputDataPerms},1,1);
end
if isnumeric(outputDataPerms)
    outputDataPerms = {outputDataPerms};
end
if isstring(outputDataPerms) && isscalar(outputDataPerms) || ischar(outputDataPerms)
    outputDataPerms = repmat({outputDataPerms},1,numDataOutputs);
end
end

function [x_model_lstm_LSTM_2_, Training, outputDataPerms, anyDlarrayInputs] = preprocessInput(x_model_lstm_LSTM_2_, params, varargin)
% Parse input arguments
[inputDataPerms, outputDataPerms, Training] = parseInputs(x_model_lstm_LSTM_2_, 1, params, varargin{:});
anyDlarrayInputs = any(cellfun(@(x)isa(x, 'dlarray'), {x_model_lstm_LSTM_2_}));
% Make the input variables into unlabelled dlarrays:
x_model_lstm_LSTM_2_ = makeUnlabeledDlarray(x_model_lstm_LSTM_2_);
% Permute inputs if requested:
x_model_lstm_LSTM_2_ = permuteInputVar(x_model_lstm_LSTM_2_, inputDataPerms{1}, 4);
end

function [probability] = postprocessOutput(probability, outputDataPerms, anyDlarrayInputs, Training, varargin)
% Set output type:
if ~anyDlarrayInputs && ~Training
    if isdlarray(probability)
        probability = extractdata(probability);
    end
end
% Permute outputs if requested:
probability = permuteOutputVar(probability, outputDataPerms{1}, 2);
end


%% dlarray functions implementing ONNX operators:

function [D, numDimsD] = onnxMatMul(A, B, numDimsA, numDimsB)
% Implements the ONNX MatMul operator.

% If either arg is more than 2D, loop over all dimensions before the final
% 2. Inside the loop, perform matrix multiplication.

% If B is 1-D, temporarily extend it to a row vector
if numDimsB==1
    B = B(:)';
end
maxNumDims = max(numDimsA, numDimsB);
numDimsD = maxNumDims;
if maxNumDims > 2
    % sizes of matrices to be multiplied
    matSizeA        = size(A, 1:2);
    matSizeB        = size(B, 1:2);
    % size of the stack of matrices
    stackSizeA      = size(A, 3:maxNumDims);
    stackSizeB      = size(B, 3:maxNumDims);
    % final stack size
    resultStackSize = max(stackSizeA, stackSizeB);
    % full implicitly-expanded sizes
    fullSizeA       = [matSizeA resultStackSize];
    fullSizeB       = [matSizeB resultStackSize];
    resultSize      = [matSizeB(1) matSizeA(2) resultStackSize];
    % Repmat A and B up to the full stack size using implicit expansion
    A = A + zeros(fullSizeA);
    B = B + zeros(fullSizeB);
    % Reshape A and B to flatten the stack dims (all dims after the first 2)
    A2 = reshape(A, size(A,1), size(A,2), []);
    B2 = reshape(B, size(B,1), size(B,2), []);
    % Iterate down the stack dim, doing the 2d matrix multiplications
    D2 = zeros([matSizeB(1), matSizeA(2), size(A2,3)], 'like', A);
    for i = size(A2,3):-1:1
        D2(:,:,i) = B2(:,:,i) * A2(:,:,i);
    end
    % Reshape D2 to the result size (unflatten the stack dims)
    D = reshape(D2, resultSize);
else
    D = B * A;
    if numDimsA==1 || numDimsB==1
        D = D(:);
        numDimsD = 1;
    end
end
end

function [Y, numDimsY] = onnxSoftmax13(X, ONNXaxis, numDimsX)
% Implements the ONNX Softmax function:
% Softmax(input, axis) = Exp(input) / ReduceSum(Exp(input), axis=axis, keepdims=1)
% The input is constrained to floating point types.

if ONNXaxis < 0
    ONNXaxis = ONNXaxis + numDimsX;
end
DLTaxis = numDimsX - ONNXaxis;

X = X - max(X, [], DLTaxis); % Subtract max(X) for numerical stability
expX = exp(X);
dims = prepareReduceArgs(ONNXaxis, numDimsX);
Y = expX ./ sum(expX, dims);
numDimsY = numDimsX;

end
function [Y, numDimsY] = onnxSqueeze(X, ONNXAxes, numDimsX)
% Implements the ONNX Squeeze operator
if numDimsX == 0
    Y = X;
    numDimsY = numDimsX;
else
    % Find the new ONNX shape
    curOShape = size(X, numDimsX:-1:1);
    if isempty(ONNXAxes)
        newOShape = curOShape(curOShape ~= 1);
    else
        ONNXAxes(ONNXAxes<0) = ONNXAxes(ONNXAxes<0) + numDimsX;
        newOShape = curOShape;
        newOShape(ONNXAxes+1) = [];
    end
    % Get numDimsY from ONNX shape
    numDimsY  = numel(newOShape);
    newMShape = [fliplr(newOShape) ones(1, 2-numDimsY)];    % Append 1's to shape if numDims<2
    Y         = reshape(X, newMShape);
end
end

function [A, B, C, alpha, beta, numDimsY] = prepareGemmArgs(A, B, C, alpha, beta, transA, transB, numDimsC)
% Prepares arguments for implementing the ONNX Gemm operator
if transA
    A = A';
end
if transB
    B = B';
end
if numDimsC < 2
    C = C(:);   % C can be broadcast to [N M]. Make C a col vector ([N 1])
end
numDimsY = 2;
% Y=B*A because we want (AB)'=B'A', and B and A are already transposed.
end

function dims = prepareReduceArgs(ONNXAxes, numDimsX)
% Prepares arguments for implementing the ONNX Reduce operator
if isempty(ONNXAxes)
    ONNXAxes = 0:numDimsX-1;   % All axes
end
ONNXAxes(ONNXAxes<0) = ONNXAxes(ONNXAxes<0) + numDimsX;
dims = numDimsX - ONNXAxes;
end

function [perm, numDimsA] = prepareTransposeArgs(ONNXPerm, numDimsA)
% Prepares arguments for implementing the ONNX Transpose operator
if numDimsA <= 1        % Tensors of numDims 0 or 1 are unchanged by ONNX Transpose.
    perm = [];
else
    if isempty(ONNXPerm)        % Empty ONNXPerm means reverse the dimensions.
        perm = numDimsA:-1:1;
    else
        perm = numDimsA-flip(ONNXPerm);
    end
end
end

function [newShape, numDimsY] = prepareUnsqueezeArgs(X, ONNXAxes, numDimsX)
% Prepares arguments for implementing the ONNX Unsqueeze operator
numDimsY = numDimsX + numel(ONNXAxes);
ONNXAxes = extractdata(ONNXAxes);
ONNXAxes(ONNXAxes<0) = ONNXAxes(ONNXAxes<0) + numDimsY;
ONNXAxes = sort(ONNXAxes);                                              % increasing order
if numDimsY == 1
    newShape = size(X);
else
    DLTAxes  = flip(numDimsY - ONNXAxes);                                  % increasing order
    newShape = ones(1, numDimsY);
    posToSet = setdiff(1:numDimsY, DLTAxes, 'stable');
    newShape(posToSet) = size(X, 1:numel(posToSet));
end
end

%% Utility functions:

function s = appendStructs(varargin)
% s = appendStructs(s1, s2,...). Assign all fields in s1, s2,... into s.
if isempty(varargin)
    s = struct;
else
    s = varargin{1};
    for i = 2:numel(varargin)
        fromstr = varargin{i};
        fs = fieldnames(fromstr);
        for j = 1:numel(fs)
            s.(fs{j}) = fromstr.(fs{j});
        end
    end
end
end

function checkInputSize(inputShape, expectedShape, inputName)

if numel(expectedShape)==0
    % The input is a scalar
    if ~isequal(inputShape, [1 1])
        inputSizeStr = makeSizeString(inputShape);
        error(message('nnet_cnn_onnx:onnx:InputNeedsResize',inputName, "[1,1]", inputSizeStr));
    end
elseif numel(expectedShape)==1
    % The input is a vector
    if ~shapeIsColumnVector(inputShape) || ~iSizesMatch({inputShape(1)}, expectedShape)
        expectedShape{2} = 1;
        expectedSizeStr = makeSizeString(expectedShape);
        inputSizeStr = makeSizeString(inputShape);
        error(message('nnet_cnn_onnx:onnx:InputNeedsResize',inputName, expectedSizeStr, inputSizeStr));
    end
else
    % The input has 2 dimensions or more
    
    % The input dimensions have been reversed; flip them back to compare to the
    % expected ONNX shape.
    inputShape = fliplr(inputShape);
    
    % If the expected shape has fewer dims than the input shape, error.
    if numel(expectedShape) < numel(inputShape)
        expectedSizeStr = strjoin(["[", strjoin(string(expectedShape), ","), "]"], "");
        error(message('nnet_cnn_onnx:onnx:InputHasGreaterNDims', inputName, expectedSizeStr));
    end
    
    % Prepad the input shape with trailing ones up to the number of elements in
    % expectedShape
    inputShape = num2cell([ones(1, numel(expectedShape) - length(inputShape)) inputShape]);
    
    % Find the number of variable size dimensions in the expected shape
    numVariableInputs = sum(cellfun(@(x) isa(x, 'char') || isa(x, 'string'), expectedShape));
    
    % Find the number of input dimensions that are not in the expected shape
    % and cannot be represented by a variable dimension
    nonMatchingInputDims = setdiff(string(inputShape), string(expectedShape));
    numNonMatchingInputDims  = numel(nonMatchingInputDims) - numVariableInputs;
    
    expectedSizeStr = makeSizeString(expectedShape);
    inputSizeStr = makeSizeString(inputShape);
    if numNonMatchingInputDims == 0 && ~iSizesMatch(inputShape, expectedShape)
        % The actual and expected input dimensions match, but in
        % a different order. The input needs to be permuted.
        error(message('nnet_cnn_onnx:onnx:InputNeedsPermute',inputName, expectedSizeStr, inputSizeStr));
    elseif numNonMatchingInputDims > 0
        % The actual and expected input sizes do not match.
        error(message('nnet_cnn_onnx:onnx:InputNeedsResize',inputName, expectedSizeStr, inputSizeStr));
    end
end
end

function doesMatch = iSizesMatch(inputShape, expectedShape)
% Check whether the input and expected shapes match, in order.
% Size elements match if (1) the elements are equal, or (2) the expected
% size element is a variable (represented by a character vector or string)
doesMatch = true;
for i=1:numel(inputShape)
    if ~(isequal(inputShape{i},expectedShape{i}) || ischar(expectedShape{i}) || isstring(expectedShape{i}))
        doesMatch = false;
        return
    end
end
end

function sizeStr = makeSizeString(shape)
sizeStr = strjoin(["[", strjoin(string(shape), ","), "]"], "");
end

function isVec = shapeIsColumnVector(shape)
if numel(shape) == 2 && shape(2) == 1
    isVec = true;
else
    isVec = false;
end
end
function X = makeUnlabeledDlarray(X)
% Make numeric X into an unlabelled dlarray
if isa(X, 'dlarray')
    X = stripdims(X);
elseif isnumeric(X)
    if isinteger(X)
        % Make ints double so they can combine with anything without
        % reducing precision
        X = double(X);
    end
    X = dlarray(X);
end
end

function [Vars, NumDims] = packageVariables(params, inputNames, inputValues, inputNumDims)
% inputNames, inputValues are cell arrays. inputRanks is a numeric vector.
Vars = appendStructs(params.Learnables, params.Nonlearnables, params.State);
NumDims = params.NumDimensions;
% Add graph inputs
for i = 1:numel(inputNames)
    Vars.(inputNames{i}) = inputValues{i};
    NumDims.(inputNames{i}) = inputNumDims(i);
end
end

function X = permuteInputVar(X, userDataPerm, onnxNDims)
% Returns reverse-ONNX ordering
if onnxNDims == 0
    return;
elseif onnxNDims == 1 && isvector(X)
    X = X(:);
    return;
elseif isnumeric(userDataPerm)
    % Permute into reverse ONNX ordering
    if numel(userDataPerm) ~= onnxNDims
        error(message('nnet_cnn_onnx:onnx:InputPermutationSize', numel(userDataPerm), onnxNDims));
    end
    perm = fliplr(userDataPerm);
elseif isequal(userDataPerm, 'auto') && onnxNDims == 4
    % Permute MATLAB HWCN to reverse onnx (WHCN)
    perm = [2 1 3 4];
elseif isequal(userDataPerm, 'as-is')
    % Do not permute the input
    perm = 1:ndims(X);
else
    % userDataPerm is either 'none' or 'auto' with no default, which means
    % it's already in onnx ordering, so just make it reverse onnx
    perm = max(2,onnxNDims):-1:1;
end
X = permute(X, perm);
end

function Y = permuteOutputVar(Y, userDataPerm, onnxNDims)
switch onnxNDims
    case 0
        perm = [];
    case 1
        if isnumeric(userDataPerm)
            % Use the user's permutation because Y is a column vector which
            % already matches ONNX.
            perm = userDataPerm;
        elseif isequal(userDataPerm, 'auto')
            % Treat the 1D onnx vector as a 2D column and transpose it
            perm = [2 1];
        else
            % userDataPerm is 'none'. Leave Y alone because it already
            % matches onnx.
            perm = [];
        end
    otherwise
        % ndims >= 2
        if isnumeric(userDataPerm)
            % Use the inverse of the user's permutation. This is not just the
            % flip of the permutation vector.
            perm = onnxNDims + 1 - userDataPerm;
        elseif isequal(userDataPerm, 'auto')
            if onnxNDims == 2
                % Permute reverse ONNX CN to DLT CN (do nothing)
                perm = [];
            elseif onnxNDims == 4
                % Permute reverse onnx (WHCN) to MATLAB HWCN
                perm = [2 1 3 4];
            else
                % User wants the output in ONNX ordering, so just reverse it from
                % reverse onnx
                perm = onnxNDims:-1:1;
            end
        elseif isequal(userDataPerm, 'as-is')
            % Do not permute the input
            perm = 1:ndims(Y);
        else
            % userDataPerm is 'none', so just make it reverse onnx
            perm = onnxNDims:-1:1;
        end
end
if ~isempty(perm)
    Y = permute(Y, perm);
end
end

function s = updateStruct(s, t)
% Set all existing fields in s from fields in t, ignoring extra fields in t.
for name = transpose(fieldnames(s))
    s.(name{1}) = t.(name{1});
end
end
