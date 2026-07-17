classdef Squeeze_To_SigmoidLayer1022 < nnet.layer.Layer & nnet.layer.Formattable
    % A custom layer auto-generated while importing an ONNX network.
    
    %#codegen
    %#ok<*PROPLC>
    %#ok<*NBRAK>
    %#ok<*INUSL>
    %#ok<*VARARG>
    
    properties (Learnable)
        base_model_classif_1
        base_model_classif_2
        base_model_classif_3
        base_model_classifie
        onnx__MatMul_245
        onnx__ReduceSum_193
        x_Constant_output_0
        x_base_model_Constan
        x_base_model_laye_3
        x_base_model_lstm_8
    end
    
    properties
        ONNXParams         % An ONNXParameters object containing parameters used by this layer.
    end
    
    methods
        function this = Squeeze_To_SigmoidLayer1022(name, onnxParams)
            this.Name = name;
            this.OutputNames = {'output'};
            this.ONNXParams = onnxParams;
            this.base_model_classif_1 = onnxParams.Learnables.base_model_classif_1;
            this.base_model_classif_2 = onnxParams.Learnables.base_model_classif_2;
            this.base_model_classif_3 = onnxParams.Learnables.base_model_classif_3;
            this.base_model_classifie = onnxParams.Learnables.base_model_classifie;
            this.onnx__MatMul_245 = onnxParams.Learnables.onnx__MatMul_245;
            this.onnx__ReduceSum_193 = onnxParams.Learnables.onnx__ReduceSum_193;
            this.x_Constant_output_0 = onnxParams.Learnables.x_Constant_output_0;
            this.x_base_model_Constan = onnxParams.Learnables.x_base_model_Constan;
            this.x_base_model_laye_3 = onnxParams.Learnables.x_base_model_laye_3;
            this.x_base_model_lstm_8 = onnxParams.Learnables.x_base_model_lstm_8;
        end
        
        function [output] = predict(this, x_base_model_lstm_LS)
            if isdlarray(x_base_model_lstm_LS)
                x_base_model_lstm_LS = stripdims(x_base_model_lstm_LS);
            end
            x_base_model_lstm_LSNumDims = 4;
            onnxParams = this.ONNXParams;
            onnxParams.Learnables.base_model_classif_1 = this.base_model_classif_1;
            onnxParams.Learnables.base_model_classif_2 = this.base_model_classif_2;
            onnxParams.Learnables.base_model_classif_3 = this.base_model_classif_3;
            onnxParams.Learnables.base_model_classifie = this.base_model_classifie;
            onnxParams.Learnables.onnx__MatMul_245 = this.onnx__MatMul_245;
            onnxParams.Learnables.onnx__ReduceSum_193 = this.onnx__ReduceSum_193;
            onnxParams.Learnables.x_Constant_output_0 = this.x_Constant_output_0;
            onnxParams.Learnables.x_base_model_Constan = this.x_base_model_Constan;
            onnxParams.Learnables.x_base_model_laye_3 = this.x_base_model_laye_3;
            onnxParams.Learnables.x_base_model_lstm_8 = this.x_base_model_lstm_8;
            [output, outputNumDims] = Squeeze_To_SigmoidFcn(x_base_model_lstm_LS, x_base_model_lstm_LSNumDims, onnxParams, 'Training', false, ...
                'InputDataPermutation', {[3 4 2 1], ['as-is']}, ...
                'OutputDataPermutation', {['as-is'], ['as-is']});
            if any(cellfun(@(A)~isnumeric(A), {output}))
                fprintf('Runtime error in network. The custom layer ''%s'' output a non-numeric value.\n', 'Squeeze_To_SigmoidLayer1022');
                error(message('nnet_cnn_onnx:onnx:BadCustomLayerRuntimeOutput', 'Squeeze_To_SigmoidLayer1022'));
            end
            output = dlarray(single(output), repmat('U', 1, max(2, outputNumDims)));
            if ~coder.target('MATLAB')
                output = extractdata(output);
            end
        end
        
        function [output] = forward(this, x_base_model_lstm_LS)
            if isdlarray(x_base_model_lstm_LS)
                x_base_model_lstm_LS = stripdims(x_base_model_lstm_LS);
            end
            x_base_model_lstm_LSNumDims = 4;
            onnxParams = this.ONNXParams;
            onnxParams.Learnables.base_model_classif_1 = this.base_model_classif_1;
            onnxParams.Learnables.base_model_classif_2 = this.base_model_classif_2;
            onnxParams.Learnables.base_model_classif_3 = this.base_model_classif_3;
            onnxParams.Learnables.base_model_classifie = this.base_model_classifie;
            onnxParams.Learnables.onnx__MatMul_245 = this.onnx__MatMul_245;
            onnxParams.Learnables.onnx__ReduceSum_193 = this.onnx__ReduceSum_193;
            onnxParams.Learnables.x_Constant_output_0 = this.x_Constant_output_0;
            onnxParams.Learnables.x_base_model_Constan = this.x_base_model_Constan;
            onnxParams.Learnables.x_base_model_laye_3 = this.x_base_model_laye_3;
            onnxParams.Learnables.x_base_model_lstm_8 = this.x_base_model_lstm_8;
            [output, outputNumDims] = Squeeze_To_SigmoidFcn(x_base_model_lstm_LS, x_base_model_lstm_LSNumDims, onnxParams, 'Training', true, ...
                'InputDataPermutation', {[3 4 2 1], ['as-is']}, ...
                'OutputDataPermutation', {['as-is'], ['as-is']});
            if any(cellfun(@(A)~isnumeric(A), {output}))
                fprintf('Runtime error in network. The custom layer ''%s'' output a non-numeric value.\n', 'Squeeze_To_SigmoidLayer1022');
                error(message('nnet_cnn_onnx:onnx:BadCustomLayerRuntimeOutput', 'Squeeze_To_SigmoidLayer1022'));
            end
            output = dlarray(single(output), repmat('U', 1, max(2, outputNumDims)));
            if ~coder.target('MATLAB')
                output = extractdata(output);
            end
        end
    end
end

function [output, outputNumDims, state] = Squeeze_To_SigmoidFcn(x_base_model_lstm_LS, x_base_model_lstm_LSNumDims, params, varargin)
%SQUEEZE_TO_SIGMOIDFCN Function implementing an imported ONNX network.
%
% THIS FILE WAS AUTO-GENERATED BY importONNXFunction.
% ONNX Operator Set Version: 14
%
% Variable names in this function are taken from the original ONNX file.
%
% [OUTPUT] = Squeeze_To_SigmoidFcn(X_BASE_MODEL_LSTM_LS, PARAMS)
%			- Evaluates the imported ONNX network SQUEEZE_TO_SIGMOIDFCN with input(s)
%			X_BASE_MODEL_LSTM_LS and the imported network parameters in PARAMS. Returns
%			network output(s) in OUTPUT.
%
% [OUTPUT, STATE] = Squeeze_To_SigmoidFcn(X_BASE_MODEL_LSTM_LS, PARAMS)
%			- Additionally returns state variables in STATE. When training,
%			use this form and set TRAINING to true.
%
% [__] = Squeeze_To_SigmoidFcn(X_BASE_MODEL_LSTM_LS, PARAMS, 'NAME1', VAL1, 'NAME2', VAL2, ...)
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
% X_BASE_MODEL_LSTM_LS
%			- Input(s) to the ONNX network.
%			  The input size(s) expected by the ONNX file are:
%				  X_BASE_MODEL_LSTM_LS:		[Unknown, Unknown, Unknown, Unknown]				Type: FLOAT
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
% OUTPUT
%			- Output(s) of the ONNX network.
%			  Without permutation, the size(s) of the outputs are:
%				  OUTPUT:		[1, sequence_length]				Type: FLOAT
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
[x_base_model_lstm_LS, Training, outputDataPerms, anyDlarrayInputs] = preprocessInput(x_base_model_lstm_LS, params, varargin{:});
% Put all variables into a single struct to implement dynamic scoping:
[Vars, NumDims] = packageVariables(params, {'x_base_model_lstm_LS'}, {x_base_model_lstm_LS}, [x_base_model_lstm_LSNumDims]);
% Call the top-level graph function:
[output, outputNumDims, state] = Squeeze_To_SigmoidGraph1012(x_base_model_lstm_LS, NumDims.x_base_model_lstm_LS, Vars, NumDims, Training, params.State);
% Postprocess the output data
[output] = postprocessOutput(output, outputDataPerms, anyDlarrayInputs, Training, varargin{:});
end

function [output, outputNumDims1021, state] = Squeeze_To_SigmoidGraph1012(x_base_model_lstm_LS, x_base_model_lstm_LSNumDims1020, Vars, NumDims, Training, state)
% Function implementing the graph 'Squeeze_To_SigmoidGraph1012'
% Update Vars and NumDims from the graph's formal input parameters. Note that state variables are already in Vars.
Vars.x_base_model_lstm_LS = x_base_model_lstm_LS;
NumDims.x_base_model_lstm_LS = x_base_model_lstm_LSNumDims1020;

% Execute the operators:
% Squeeze:
[Vars.x_base_model_lstm_Sq, NumDims.x_base_model_lstm_Sq] = onnxSqueeze(Vars.x_base_model_lstm_LS, Vars.x_base_model_lstm_8, NumDims.x_base_model_lstm_LS);

% Transpose:
[perm, NumDims.x_base_model_lstm_Tr] = prepareTransposeArgs(Vars.TransposePerm1013, NumDims.x_base_model_lstm_Sq);
if ~isempty(perm)
    Vars.x_base_model_lstm_Tr = permute(Vars.x_base_model_lstm_Sq, perm);
end

% ReduceMean:
dims = prepareReduceArgs(Vars.ReduceMeanAxes1014, NumDims.x_base_model_lstm_Tr);
Vars.x_base_model_laye_8 = mean(Vars.x_base_model_lstm_Tr, dims);
NumDims.x_base_model_laye_8 = NumDims.x_base_model_lstm_Tr;

% Sub:
Vars.x_base_model_laye_10 = Vars.x_base_model_lstm_Tr - Vars.x_base_model_laye_8;
NumDims.x_base_model_laye_10 = max(NumDims.x_base_model_lstm_Tr, NumDims.x_base_model_laye_8);

% Pow:
Vars.x_base_model_laye_6 = power(Vars.x_base_model_laye_10, Vars.x_base_model_laye_3);
NumDims.x_base_model_laye_6 = max(NumDims.x_base_model_laye_10, NumDims.x_base_model_laye_3);

% ReduceMean:
dims = prepareReduceArgs(Vars.ReduceMeanAxes1015, NumDims.x_base_model_laye_6);
Vars.x_base_model_laye_7 = mean(Vars.x_base_model_laye_6, dims);
NumDims.x_base_model_laye_7 = NumDims.x_base_model_laye_6;

% Add:
Vars.x_base_model_laye_1 = Vars.x_base_model_laye_7 + Vars.x_base_model_laye_2;
NumDims.x_base_model_laye_1 = max(NumDims.x_base_model_laye_7, NumDims.x_base_model_laye_2);

% Sqrt:
Vars.x_base_model_laye_9 = sqrt(Vars.x_base_model_laye_1);
NumDims.x_base_model_laye_9 = NumDims.x_base_model_laye_1;

% Div:
Vars.x_base_model_laye_4 = Vars.x_base_model_laye_10 ./ Vars.x_base_model_laye_9;
NumDims.x_base_model_laye_4 = max(NumDims.x_base_model_laye_10, NumDims.x_base_model_laye_9);

% Mul:
Vars.x_base_model_laye_5 = Vars.x_base_model_laye_4 .* Vars.base_model_layer_n_1;
NumDims.x_base_model_laye_5 = max(NumDims.x_base_model_laye_4, NumDims.base_model_layer_n_1);

% Add:
Vars.x_base_model_layer_n = Vars.x_base_model_laye_5 + Vars.base_model_layer_nor;
NumDims.x_base_model_layer_n = max(NumDims.x_base_model_laye_5, NumDims.base_model_layer_nor);

% MatMul:
[Vars.x_base_model_atten_1, NumDims.x_base_model_atten_1] = onnxMatMul(Vars.x_base_model_layer_n, Vars.onnx__MatMul_245, NumDims.x_base_model_layer_n, NumDims.onnx__MatMul_245);

% Add:
Vars.x_base_model_attenti = Vars.base_model_attention + Vars.x_base_model_atten_1;
NumDims.x_base_model_attenti = max(NumDims.base_model_attention, NumDims.x_base_model_atten_1);

% Softmax:
[Vars.x_base_model_Softmax, NumDims.x_base_model_Softmax] = onnxSoftmax13(Vars.x_base_model_attenti, 1, NumDims.x_base_model_attenti);

% Mul:
Vars.x_base_model_Mul_out = Vars.x_base_model_Softmax .* Vars.x_base_model_layer_n;
NumDims.x_base_model_Mul_out = max(NumDims.x_base_model_Softmax, NumDims.x_base_model_layer_n);

% ReduceSum:
dims = prepareReduceArgs(Vars.onnx__ReduceSum_193, NumDims.x_base_model_Mul_out);
Vars.x_base_model_ReduceS = sum(Vars.x_base_model_Mul_out, dims);
[Vars.x_base_model_ReduceS, NumDims.x_base_model_ReduceS] = onnxSqueeze(Vars.x_base_model_ReduceS, Vars.onnx__ReduceSum_193, NumDims.x_base_model_Mul_out);

% Gemm:
[A, B, C, alpha, beta, NumDims.x_base_model_classif] = prepareGemmArgs(Vars.x_base_model_ReduceS, Vars.base_model_classif_1, Vars.base_model_classifie, Vars.Gemmalpha1016, Vars.Gemmbeta1017, 0, 1, NumDims.base_model_classifie);
Vars.x_base_model_classif = alpha*B*A + beta*C;

% Relu:
Vars.x_base_model_class_1 = relu(Vars.x_base_model_classif);
NumDims.x_base_model_class_1 = NumDims.x_base_model_classif;

% Gemm:
[A, B, C, alpha, beta, NumDims.x_base_model_class_2] = prepareGemmArgs(Vars.x_base_model_class_1, Vars.base_model_classif_3, Vars.base_model_classif_2, Vars.Gemmalpha1018, Vars.Gemmbeta1019, 0, 1, NumDims.base_model_classif_2);
Vars.x_base_model_class_2 = alpha*B*A + beta*C;

% Squeeze:
[Vars.x_base_model_Squeeze, NumDims.x_base_model_Squeeze] = onnxSqueeze(Vars.x_base_model_class_2, Vars.x_base_model_Constan, NumDims.x_base_model_class_2);

% Unsqueeze:
[shape, NumDims.x_Unsqueeze_output_0] = prepareUnsqueezeArgs(Vars.x_base_model_Squeeze, Vars.x_Constant_output_0, NumDims.x_base_model_Squeeze);
Vars.x_Unsqueeze_output_0 = reshape(Vars.x_base_model_Squeeze, shape);

% Sigmoid:
Vars.output = sigmoid(Vars.x_Unsqueeze_output_0);
NumDims.output = NumDims.x_Unsqueeze_output_0;

% Set graph output arguments from Vars and NumDims:
output = Vars.output;
outputNumDims1021 = NumDims.output;
% Set output state from Vars:
state = updateStruct(state, Vars);
end

function [inputDataPerms, outputDataPerms, Training] = parseInputs(x_base_model_lstm_LS, numDataOutputs, params, varargin)
% Function to validate inputs to Squeeze_To_SigmoidFcn:
p = inputParser;
isValidArrayInput = @(x)isnumeric(x) || isstring(x);
isValidONNXParameters = @(x)isa(x, 'ONNXParameters');
addRequired(p, 'x_base_model_lstm_LS', isValidArrayInput);
addRequired(p, 'params', isValidONNXParameters);
addParameter(p, 'InputDataPermutation', 'auto');
addParameter(p, 'OutputDataPermutation', 'auto');
addParameter(p, 'Training', false);
parse(p, x_base_model_lstm_LS, params, varargin{:});
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

function [x_base_model_lstm_LS, Training, outputDataPerms, anyDlarrayInputs] = preprocessInput(x_base_model_lstm_LS, params, varargin)
% Parse input arguments
[inputDataPerms, outputDataPerms, Training] = parseInputs(x_base_model_lstm_LS, 1, params, varargin{:});
anyDlarrayInputs = any(cellfun(@(x)isa(x, 'dlarray'), {x_base_model_lstm_LS}));
% Make the input variables into unlabelled dlarrays:
x_base_model_lstm_LS = makeUnlabeledDlarray(x_base_model_lstm_LS);
% Permute inputs if requested:
x_base_model_lstm_LS = permuteInputVar(x_base_model_lstm_LS, inputDataPerms{1}, 4);
end

function [output] = postprocessOutput(output, outputDataPerms, anyDlarrayInputs, Training, varargin)
% Set output type:
if ~anyDlarrayInputs && ~Training
    if isdlarray(output)
        output = extractdata(output);
    end
end
% Permute outputs if requested:
output = permuteOutputVar(output, outputDataPerms{1}, 2);
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
