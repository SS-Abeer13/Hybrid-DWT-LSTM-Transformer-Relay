classdef Shape_To_SliceLayer1007 < nnet.layer.Layer & nnet.layer.Formattable
    % A custom layer auto-generated while importing an ONNX network.
    
    %#codegen
    %#ok<*PROPLC>
    %#ok<*NBRAK>
    %#ok<*INUSL>
    %#ok<*VARARG>
    
    properties (Learnable)
        onnx__Unsqueeze_22
    end
    
    properties
        ONNXParams         % An ONNXParameters object containing parameters used by this layer.
    end
    
    methods
        function this = Shape_To_SliceLayer1007(name, onnxParams)
            this.Name = name;
            this.NumOutputs = 4;
            this.OutputNames = {'x_lstm_Slice_output_', 'x_lstm_Slice_1_outpu', 'x_lstm_Slice_2_outpu', 'x_lstm_Slice_3_outpu'};
            this.ONNXParams = onnxParams;
            this.onnx__Unsqueeze_22 = onnxParams.Learnables.onnx__Unsqueeze_22;
        end
        
        function [x_lstm_Slice_output_, x_lstm_Slice_1_outpu, x_lstm_Slice_2_outpu, x_lstm_Slice_3_outpu] = predict(this, input)
            if isdlarray(input)
                input = stripdims(input);
            end
            inputNumDims = 3;
            onnxParams = this.ONNXParams;
            onnxParams.Learnables.onnx__Unsqueeze_22 = this.onnx__Unsqueeze_22;
            [x_lstm_Slice_output_, x_lstm_Slice_1_outpu, x_lstm_Slice_2_outpu, x_lstm_Slice_3_outpu, x_lstm_Slice_output_NumDims, x_lstm_Slice_1_outpuNumDims, x_lstm_Slice_2_outpuNumDims, x_lstm_Slice_3_outpuNumDims] = Shape_To_SliceFcn(input, inputNumDims, onnxParams, 'Training', false, ...
                'InputDataPermutation', {[2 3 1], ['as-is']}, ...
                'OutputDataPermutation', {[3 2 1], [3 2 1], [3 2 1], [3 2 1], ['as-is'], ['as-is'], ['as-is'], ['as-is']});
            if any(cellfun(@(A)~isnumeric(A), {x_lstm_Slice_output_, x_lstm_Slice_1_outpu, x_lstm_Slice_2_outpu, x_lstm_Slice_3_outpu}))
                fprintf('Runtime error in network. The custom layer ''%s'' output a non-numeric value.\n', 'Shape_To_SliceLayer1007');
                error(message('nnet_cnn_onnx:onnx:BadCustomLayerRuntimeOutput', 'Shape_To_SliceLayer1007'));
            end
            x_lstm_Slice_output_ = dlarray(single(x_lstm_Slice_output_), 'CB');
            x_lstm_Slice_1_outpu = dlarray(single(x_lstm_Slice_1_outpu), 'CB');
            x_lstm_Slice_2_outpu = dlarray(single(x_lstm_Slice_2_outpu), 'CB');
            x_lstm_Slice_3_outpu = dlarray(single(x_lstm_Slice_3_outpu), 'CB');
            if ~coder.target('MATLAB')
                x_lstm_Slice_output_ = extractdata(x_lstm_Slice_output_);
                x_lstm_Slice_1_outpu = extractdata(x_lstm_Slice_1_outpu);
                x_lstm_Slice_2_outpu = extractdata(x_lstm_Slice_2_outpu);
                x_lstm_Slice_3_outpu = extractdata(x_lstm_Slice_3_outpu);
            end
        end
        
        function [x_lstm_Slice_output_, x_lstm_Slice_1_outpu, x_lstm_Slice_2_outpu, x_lstm_Slice_3_outpu] = forward(this, input)
            if isdlarray(input)
                input = stripdims(input);
            end
            inputNumDims = 3;
            onnxParams = this.ONNXParams;
            onnxParams.Learnables.onnx__Unsqueeze_22 = this.onnx__Unsqueeze_22;
            [x_lstm_Slice_output_, x_lstm_Slice_1_outpu, x_lstm_Slice_2_outpu, x_lstm_Slice_3_outpu, x_lstm_Slice_output_NumDims, x_lstm_Slice_1_outpuNumDims, x_lstm_Slice_2_outpuNumDims, x_lstm_Slice_3_outpuNumDims] = Shape_To_SliceFcn(input, inputNumDims, onnxParams, 'Training', true, ...
                'InputDataPermutation', {[2 3 1], ['as-is']}, ...
                'OutputDataPermutation', {[3 2 1], [3 2 1], [3 2 1], [3 2 1], ['as-is'], ['as-is'], ['as-is'], ['as-is']});
            if any(cellfun(@(A)~isnumeric(A), {x_lstm_Slice_output_, x_lstm_Slice_1_outpu, x_lstm_Slice_2_outpu, x_lstm_Slice_3_outpu}))
                fprintf('Runtime error in network. The custom layer ''%s'' output a non-numeric value.\n', 'Shape_To_SliceLayer1007');
                error(message('nnet_cnn_onnx:onnx:BadCustomLayerRuntimeOutput', 'Shape_To_SliceLayer1007'));
            end
            x_lstm_Slice_output_ = dlarray(single(x_lstm_Slice_output_), 'CB');
            x_lstm_Slice_1_outpu = dlarray(single(x_lstm_Slice_1_outpu), 'CB');
            x_lstm_Slice_2_outpu = dlarray(single(x_lstm_Slice_2_outpu), 'CB');
            x_lstm_Slice_3_outpu = dlarray(single(x_lstm_Slice_3_outpu), 'CB');
            if ~coder.target('MATLAB')
                x_lstm_Slice_output_ = extractdata(x_lstm_Slice_output_);
                x_lstm_Slice_1_outpu = extractdata(x_lstm_Slice_1_outpu);
                x_lstm_Slice_2_outpu = extractdata(x_lstm_Slice_2_outpu);
                x_lstm_Slice_3_outpu = extractdata(x_lstm_Slice_3_outpu);
            end
        end
    end
end

function [x_lstm_Slice_output_, x_lstm_Slice_1_outpu, x_lstm_Slice_2_outpu, x_lstm_Slice_3_outpu, x_lstm_Slice_output_NumDims, x_lstm_Slice_1_outpuNumDims, x_lstm_Slice_2_outpuNumDims, x_lstm_Slice_3_outpuNumDims, state] = Shape_To_SliceFcn(input, inputNumDims, params, varargin)
%SHAPE_TO_SLICEFCN Function implementing an imported ONNX network.
%
% THIS FILE WAS AUTO-GENERATED BY importONNXFunction.
% ONNX Operator Set Version: 14
%
% Variable names in this function are taken from the original ONNX file.
%
% [X_LSTM_SLICE_OUTPUT_, X_LSTM_SLICE_1_OUTPU, X_LSTM_SLICE_2_OUTPU, X_LSTM_SLICE_3_OUTPU] = Shape_To_SliceFcn(INPUT, PARAMS)
%			- Evaluates the imported ONNX network SHAPE_TO_SLICEFCN with input(s)
%			INPUT and the imported network parameters in PARAMS. Returns
%			network output(s) in X_LSTM_SLICE_OUTPUT_, X_LSTM_SLICE_1_OUTPU, X_LSTM_SLICE_2_OUTPU, X_LSTM_SLICE_3_OUTPU.
%
% [X_LSTM_SLICE_OUTPUT_, X_LSTM_SLICE_1_OUTPU, X_LSTM_SLICE_2_OUTPU, X_LSTM_SLICE_3_OUTPU, STATE] = Shape_To_SliceFcn(INPUT, PARAMS)
%			- Additionally returns state variables in STATE. When training,
%			use this form and set TRAINING to true.
%
% [__] = Shape_To_SliceFcn(INPUT, PARAMS, 'NAME1', VAL1, 'NAME2', VAL2, ...)
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
% INPUT
%			- Input(s) to the ONNX network.
%			  The input size(s) expected by the ONNX file are:
%				  INPUT:		[1, sequence_length, 6]				Type: FLOAT
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
% X_LSTM_SLICE_OUTPUT_, X_LSTM_SLICE_1_OUTPU, X_LSTM_SLICE_2_OUTPU, X_LSTM_SLICE_3_OUTPU
%			- Output(s) of the ONNX network.
%			  Without permutation, the size(s) of the outputs are:
%				  X_LSTM_SLICE_OUTPUT_:		[Unknown, Unknown, Unknown]				Type: FLOAT
%				  X_LSTM_SLICE_1_OUTPU:		[Unknown, Unknown, Unknown]				Type: FLOAT
%				  X_LSTM_SLICE_2_OUTPU:		[Unknown, Unknown, Unknown]				Type: FLOAT
%				  X_LSTM_SLICE_3_OUTPU:		[Unknown, Unknown, Unknown]				Type: FLOAT
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
[input, Training, outputDataPerms, anyDlarrayInputs] = preprocessInput(input, params, varargin{:});
% Put all variables into a single struct to implement dynamic scoping:
[Vars, NumDims] = packageVariables(params, {'input'}, {input}, [inputNumDims]);
% Call the top-level graph function:
[x_lstm_Slice_output_, x_lstm_Slice_1_outpu, x_lstm_Slice_2_outpu, x_lstm_Slice_3_outpu, x_lstm_Slice_output_NumDims, x_lstm_Slice_1_outpuNumDims, x_lstm_Slice_2_outpuNumDims, x_lstm_Slice_3_outpuNumDims, state] = Shape_To_SliceGraph1000(input, NumDims.input, Vars, NumDims, Training, params.State);
% Postprocess the output data
[x_lstm_Slice_output_, x_lstm_Slice_1_outpu, x_lstm_Slice_2_outpu, x_lstm_Slice_3_outpu] = postprocessOutput(x_lstm_Slice_output_, x_lstm_Slice_1_outpu, x_lstm_Slice_2_outpu, x_lstm_Slice_3_outpu, outputDataPerms, anyDlarrayInputs, Training, varargin{:});
end

function [x_lstm_Slice_output_, x_lstm_Slice_1_outpu, x_lstm_Slice_2_outpu, x_lstm_Slice_3_outpu, x_lstm_Slice_output_NumDims1003, x_lstm_Slice_1_outpuNumDims1004, x_lstm_Slice_2_outpuNumDims1005, x_lstm_Slice_3_outpuNumDims1006, state] = Shape_To_SliceGraph1000(input, inputNumDims1002, Vars, NumDims, Training, state)
% Function implementing the graph 'Shape_To_SliceGraph1000'
% Update Vars and NumDims from the graph's formal input parameters. Note that state variables are already in Vars.
Vars.input = input;
NumDims.input = inputNumDims1002;

% Execute the operators:
% Shape:
[Vars.x_lstm_Shape_output_, NumDims.x_lstm_Shape_output_] = onnxShape(Vars.input, NumDims.input);

% Gather:
[Vars.x_lstm_Gather_output, NumDims.x_lstm_Gather_output] = onnxGather(Vars.x_lstm_Shape_output_, Vars.x_lstm_Constant_outp, 0, NumDims.x_lstm_Shape_output_, NumDims.x_lstm_Constant_outp);

% Unsqueeze:
[shape, NumDims.x_lstm_Unsqueeze_out] = prepareUnsqueezeArgs(Vars.x_lstm_Gather_output, Vars.onnx__Unsqueeze_22, NumDims.x_lstm_Gather_output);
Vars.x_lstm_Unsqueeze_out = reshape(Vars.x_lstm_Gather_output, shape);

% Concat:
[Vars.x_lstm_Concat_output, NumDims.x_lstm_Concat_output] = onnxConcat(0, {Vars.x_lstm_Constant_1_ou, Vars.x_lstm_Unsqueeze_out, Vars.x_lstm_Constant_2_ou}, [NumDims.x_lstm_Constant_1_ou, NumDims.x_lstm_Unsqueeze_out, NumDims.x_lstm_Constant_2_ou]);

% ConstantOfShape:
[Vars.x_lstm_ConstantOfSha, NumDims.x_lstm_ConstantOfSha] = onnxConstantOfShape(Vars.ConstantOfShapeValue1001, Vars.x_lstm_Concat_output);

% Slice:
[Indices, NumDims.x_lstm_Slice_output_] = prepareSliceArgs(Vars.x_lstm_ConstantOfSha, Vars.x_lstm_Constant_4_ou, Vars.x_lstm_Constant_5_ou, Vars.x_lstm_Constant_3_ou, '', NumDims.x_lstm_ConstantOfSha);
Vars.x_lstm_Slice_output_ = subsref(Vars.x_lstm_ConstantOfSha, Indices);

% Slice:
[Indices, NumDims.x_lstm_Slice_1_outpu] = prepareSliceArgs(Vars.x_lstm_ConstantOfSha, Vars.x_lstm_Constant_7_ou, Vars.x_lstm_Constant_8_ou, Vars.x_lstm_Constant_6_ou, '', NumDims.x_lstm_ConstantOfSha);
Vars.x_lstm_Slice_1_outpu = subsref(Vars.x_lstm_ConstantOfSha, Indices);

% Slice:
[Indices, NumDims.x_lstm_Slice_2_outpu] = prepareSliceArgs(Vars.x_lstm_ConstantOfSha, Vars.x_lstm_Constant_11_o, Vars.x_lstm_Constant_12_o, Vars.x_lstm_Constant_10_o, '', NumDims.x_lstm_ConstantOfSha);
Vars.x_lstm_Slice_2_outpu = subsref(Vars.x_lstm_ConstantOfSha, Indices);

% Slice:
[Indices, NumDims.x_lstm_Slice_3_outpu] = prepareSliceArgs(Vars.x_lstm_ConstantOfSha, Vars.x_lstm_Constant_14_o, Vars.x_lstm_Constant_15_o, Vars.x_lstm_Constant_13_o, '', NumDims.x_lstm_ConstantOfSha);
Vars.x_lstm_Slice_3_outpu = subsref(Vars.x_lstm_ConstantOfSha, Indices);

% Set graph output arguments from Vars and NumDims:
x_lstm_Slice_output_ = Vars.x_lstm_Slice_output_;
x_lstm_Slice_output_NumDims1003 = NumDims.x_lstm_Slice_output_;
x_lstm_Slice_1_outpu = Vars.x_lstm_Slice_1_outpu;
x_lstm_Slice_1_outpuNumDims1004 = NumDims.x_lstm_Slice_1_outpu;
x_lstm_Slice_2_outpu = Vars.x_lstm_Slice_2_outpu;
x_lstm_Slice_2_outpuNumDims1005 = NumDims.x_lstm_Slice_2_outpu;
x_lstm_Slice_3_outpu = Vars.x_lstm_Slice_3_outpu;
x_lstm_Slice_3_outpuNumDims1006 = NumDims.x_lstm_Slice_3_outpu;
% Set output state from Vars:
state = updateStruct(state, Vars);
end

function [inputDataPerms, outputDataPerms, Training] = parseInputs(input, numDataOutputs, params, varargin)
% Function to validate inputs to Shape_To_SliceFcn:
p = inputParser;
isValidArrayInput = @(x)isnumeric(x) || isstring(x);
isValidONNXParameters = @(x)isa(x, 'ONNXParameters');
addRequired(p, 'input', isValidArrayInput);
addRequired(p, 'params', isValidONNXParameters);
addParameter(p, 'InputDataPermutation', 'auto');
addParameter(p, 'OutputDataPermutation', 'auto');
addParameter(p, 'Training', false);
parse(p, input, params, varargin{:});
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

function [input, Training, outputDataPerms, anyDlarrayInputs] = preprocessInput(input, params, varargin)
% Parse input arguments
[inputDataPerms, outputDataPerms, Training] = parseInputs(input, 4, params, varargin{:});
anyDlarrayInputs = any(cellfun(@(x)isa(x, 'dlarray'), {input}));
% Make the input variables into unlabelled dlarrays:
input = makeUnlabeledDlarray(input);
% Permute inputs if requested:
input = permuteInputVar(input, inputDataPerms{1}, 3);
end

function [x_lstm_Slice_output_, x_lstm_Slice_1_outpu, x_lstm_Slice_2_outpu, x_lstm_Slice_3_outpu] = postprocessOutput(x_lstm_Slice_output_, x_lstm_Slice_1_outpu, x_lstm_Slice_2_outpu, x_lstm_Slice_3_outpu, outputDataPerms, anyDlarrayInputs, Training, varargin)
% Set output type:
if ~anyDlarrayInputs && ~Training
    if isdlarray(x_lstm_Slice_output_)
        x_lstm_Slice_output_ = extractdata(x_lstm_Slice_output_);
    end
    if isdlarray(x_lstm_Slice_1_outpu)
        x_lstm_Slice_1_outpu = extractdata(x_lstm_Slice_1_outpu);
    end
    if isdlarray(x_lstm_Slice_2_outpu)
        x_lstm_Slice_2_outpu = extractdata(x_lstm_Slice_2_outpu);
    end
    if isdlarray(x_lstm_Slice_3_outpu)
        x_lstm_Slice_3_outpu = extractdata(x_lstm_Slice_3_outpu);
    end
end
% Permute outputs if requested:
x_lstm_Slice_output_ = permuteOutputVar(x_lstm_Slice_output_, outputDataPerms{1}, 3);
x_lstm_Slice_1_outpu = permuteOutputVar(x_lstm_Slice_1_outpu, outputDataPerms{2}, 3);
x_lstm_Slice_2_outpu = permuteOutputVar(x_lstm_Slice_2_outpu, outputDataPerms{3}, 3);
x_lstm_Slice_3_outpu = permuteOutputVar(x_lstm_Slice_3_outpu, outputDataPerms{4}, 3);
end


%% dlarray functions implementing ONNX operators:

function [Y, numDimsY] = onnxConcat(ONNXAxis, XCell, numDimsXArray)
% Concatentation that treats all empties the same. Necessary because
% dlarray.cat does not allow, for example, cat(1, 1x1, 1x0) because the
% second dimension sizes do not match.
numDimsY = numDimsXArray(1);
XCell(cellfun(@isempty, XCell)) = [];
if isempty(XCell)
    Y = dlarray([]);
else
    if ONNXAxis<0
        ONNXAxis = ONNXAxis + numDimsY;
    end
    DLTAxis = numDimsY - ONNXAxis;
    Y = cat(DLTAxis, XCell{:});
end
end

function [Y, numDimsY] = onnxConstantOfShape(value, ONNXShape)
% Returns a DLT tensor with the reverse of the ONNXShape.
DLTShape = fliplr(extractdata(ONNXShape(:)'));
numDimsY = numel(DLTShape);
switch numDimsY
    case 0
        % If shape is empty, output is a scalar
        Y = value;
    case 1
        Y = ones(DLTShape,1) .* value;
    otherwise
        Y = ones(DLTShape) .* value;
end
end

function [Y, numDimsY] = onnxGather(X, ONNXIdx, ONNXAxis, numDimsX, numDimsIdx)
% Function implementing the ONNX Gather operator

% In ONNX, 'Gather' first indexes into dimension ONNXAxis of data, using
% the contents of ONNXIdx as the indices. Then, it reshapes the ONNXAxis
% into the shape of ONNXIdx.
%   Example 1:
% Suppose data has shape [2 3 4 5], ONNXIdx has shape [6 7], and axis=1.
% The result has shape [2 6 7 4 5].
%   Example 2:
% Suppose data has shape [2 3 4 5], ONNXIdx has shape [6], and axis=1.
% The result has shape [2 6 4 5].
%   Example 3:
% Suppose data has shape [2 3 4 5], ONNXIdx has shape [] (a scalar), and axis=1.
% The result has shape [2 4 5].
%
% Since we're using reverse indexing relative to ONNX, in this function
% data and ONNXIdx both have reversed dimension ordering.
numDimsY = numDimsIdx + (numDimsX - 1);
if isempty(X)
    Y = X;
    return;
end
% (1) First, do the subsref part of Gather
if ONNXAxis<0
    ONNXAxis = ONNXAxis + numDimsX;                                 % Axis can be negative. Convert it to its positive equivalent.
end
dltAxis = numDimsX - ONNXAxis;                                      % Convert axis to DLT. ONNXAxis is origin 0 and we index from the end
ONNXIdx(ONNXIdx<0) = ONNXIdx(ONNXIdx<0) + size(X, dltAxis);         % ONNXIdx can have negative components. Make them positive.
dltIdx  = extractdata(ONNXIdx) + 1;                                 % ONNXIdx is origin-0 in ONNX, so add 1 to get dltIdx
% Use subsref to index into data
Indices.subs = repmat({':'}, 1, numDimsX);
Indices.subs{dltAxis} = dltIdx(:);                                  % Index as a column to ensure the output is 1-D in the indexed dimension (for now).
Indices.type = '()';
Y = subsref(X, Indices);
% (2) Now do the reshaping part of Gather
shape = size(Y, 1:numDimsX);
if numDimsIdx == 0
    % Delete the indexed dimension
    shape(dltAxis) = [];
elseif numDimsIdx > 1
    % Reshape the indexed dimension into the shape of ONNXIdx
    shape = [shape(1:dltAxis-1) size(ONNXIdx, 1:numDimsIdx) shape(dltAxis+1:end)];
end
% Extend the shape to 2D so it's valid MATLAB
if numel(shape) < 2
    shape = [shape ones(1,2-numel(shape))];
end
Y = reshape(Y, shape);
end

function [Y, numDimsY] = onnxShape(X, numDimsX)
% Implements the ONNX Shape operator
% Return the reverse ONNX shape as a 1D column vector
switch numDimsX
    case 0
        if isempty(X)
            Y = dlarray(0);
        else
            Y = dlarray(1);
        end
    case 1
        if isempty(X)
            Y = dlarray(0);
        else
            Y = dlarray(size(X,1));
        end
    otherwise
        Y = dlarray(fliplr(size(X, 1:numDimsX))');
end
numDimsY = 1;
end

function [S, numDimsY] = prepareSliceArgs(X, Starts, Ends, Axes, Steps, numDimsX)
% Prepares arguments for implementing the ONNX Slice operator

% Starts, Ends and Axes are all origin 0. Axes refer to the ONNX dimension
% ordering, but X uses the reverse, DLT ordering. Starts, Ends, Axes, and
% Steps correspond positionally. Axes and Steps may be omitted, with
% defaults described in the ONNX spec.

% Set default Axes and Steps if not supplied
if isempty(Axes)
    Axes = 0:numDimsX-1;   % All axes
end
Axes(Axes<0) = Axes(Axes<0) + numDimsX; % Handle negative Axes.
if isempty(Steps)
    Steps = ones(1, numel(Starts));
end
% Init all dims to :
S.subs = repmat({':'}, 1, numDimsX);
S.type = '()';
% Set Starts and Ends for each axis
for i = 1:numel(Axes)
    DLTDim = numDimsX - Axes(i);                                               % The DLT dim is the reverse of the ONNX dim.
    % "If a negative value is passed for any of the start or end indices,
    % it represents number of elements before the end of that dimension."
    if Starts(i) < 0
        Starts(i) = size(X,DLTDim) + Starts(i);
    end
    if Ends(i) < 0
        Ends(i) = max(-1, size(X,DLTDim) + Ends(i));                        % The -1 case is when we're slicing backward and want to include 0.
    end
    % "If the value passed to start or end is larger than the n (the number
    % of elements in this dimension), it represents n."
    if Starts(i) > size(X,DLTDim)
        Starts(i) = size(X,DLTDim);
    end
    if Ends(i) > size(X,DLTDim)
        Ends(i) = size(X,DLTDim);
    end
    if Steps(i) > 0
        S.subs{DLTDim} = 1 + (Starts(i) : Steps(i) : Ends(i)-1);            % 1 + (Origin 0 indexing with end index excluded)
    else
        S.subs{DLTDim} = 1 + (Starts(i) : Steps(i) : Ends(i)+1);            % 1 + (Origin 0 indexing with end index excluded)
    end
end
numDimsY = numDimsX;
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
