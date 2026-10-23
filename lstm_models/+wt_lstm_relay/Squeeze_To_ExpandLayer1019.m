classdef Squeeze_To_ExpandLayer1019 < nnet.layer.Layer & nnet.layer.Formattable
    % A custom layer auto-generated while importing an ONNX network.
    
    %#codegen
    %#ok<*PROPLC>
    %#ok<*NBRAK>
    %#ok<*INUSL>
    %#ok<*VARARG>
    
    properties (Learnable)
        onnx__Unsqueeze_282
        onnx__Unsqueeze_293
        x_model_lstm_Cons_3
        x_model_lstm_Cons_4
        x_model_lstm_Cons_5
    end
    
    properties
        ONNXParams         % An ONNXParameters object containing parameters used by this layer.
    end
    
    methods
        function this = Squeeze_To_ExpandLayer1019(name, onnxParams)
            this.Name = name;
            this.NumOutputs = 3;
            this.OutputNames = {'x_model_lstm_Squeeze', 'x_model_lstm_Expa_3', 'x_model_lstm_Expa_4'};
            this.ONNXParams = onnxParams;
            this.onnx__Unsqueeze_282 = onnxParams.Learnables.onnx__Unsqueeze_282;
            this.onnx__Unsqueeze_293 = onnxParams.Learnables.onnx__Unsqueeze_293;
            this.x_model_lstm_Cons_3 = onnxParams.Learnables.x_model_lstm_Cons_3;
            this.x_model_lstm_Cons_4 = onnxParams.Learnables.x_model_lstm_Cons_4;
            this.x_model_lstm_Cons_5 = onnxParams.Learnables.x_model_lstm_Cons_5;
        end
        
        function [x_model_lstm_Squeeze, x_model_lstm_Expa_3, x_model_lstm_Expa_4] = predict(this, x_model_lstm_LSTM_1_)
            if isdlarray(x_model_lstm_LSTM_1_)
                x_model_lstm_LSTM_1_ = stripdims(x_model_lstm_LSTM_1_);
            end
            x_model_lstm_LSTM_1_NumDims = 4;
            onnxParams = this.ONNXParams;
            onnxParams.Learnables.onnx__Unsqueeze_282 = this.onnx__Unsqueeze_282;
            onnxParams.Learnables.onnx__Unsqueeze_293 = this.onnx__Unsqueeze_293;
            onnxParams.Learnables.x_model_lstm_Cons_3 = this.x_model_lstm_Cons_3;
            onnxParams.Learnables.x_model_lstm_Cons_4 = this.x_model_lstm_Cons_4;
            onnxParams.Learnables.x_model_lstm_Cons_5 = this.x_model_lstm_Cons_5;
            [x_model_lstm_Squeeze, x_model_lstm_Expa_3, x_model_lstm_Expa_4, x_model_lstm_SqueezeNumDims, x_model_lstm_Expa_3NumDims, x_model_lstm_Expa_4NumDims] = Squeeze_To_ExpandFcn(x_model_lstm_LSTM_1_, x_model_lstm_LSTM_1_NumDims, onnxParams, 'Training', false, ...
                'InputDataPermutation', {[3 4 2 1], ['as-is']}, ...
                'OutputDataPermutation', {[3 2 1], [3 2 1], [3 2 1], ['as-is'], ['as-is'], ['as-is']});
            if any(cellfun(@(A)~isnumeric(A), {x_model_lstm_Squeeze, x_model_lstm_Expa_3, x_model_lstm_Expa_4}))
                fprintf('Runtime error in network. The custom layer ''%s'' output a non-numeric value.\n', 'Squeeze_To_ExpandLayer1019');
                error(message('nnet_cnn_onnx:onnx:BadCustomLayerRuntimeOutput', 'Squeeze_To_ExpandLayer1019'));
            end
            x_model_lstm_Squeeze = dlarray(single(x_model_lstm_Squeeze), 'CBT');
            x_model_lstm_Expa_3 = dlarray(single(x_model_lstm_Expa_3), 'CB');
            x_model_lstm_Expa_4 = dlarray(single(x_model_lstm_Expa_4), 'CB');
            if ~coder.target('MATLAB')
                x_model_lstm_Squeeze = extractdata(x_model_lstm_Squeeze);
                x_model_lstm_Expa_3 = extractdata(x_model_lstm_Expa_3);
                x_model_lstm_Expa_4 = extractdata(x_model_lstm_Expa_4);
            end
        end
        
        function [x_model_lstm_Squeeze, x_model_lstm_Expa_3, x_model_lstm_Expa_4] = forward(this, x_model_lstm_LSTM_1_)
            if isdlarray(x_model_lstm_LSTM_1_)
                x_model_lstm_LSTM_1_ = stripdims(x_model_lstm_LSTM_1_);
            end
            x_model_lstm_LSTM_1_NumDims = 4;
            onnxParams = this.ONNXParams;
            onnxParams.Learnables.onnx__Unsqueeze_282 = this.onnx__Unsqueeze_282;
            onnxParams.Learnables.onnx__Unsqueeze_293 = this.onnx__Unsqueeze_293;
            onnxParams.Learnables.x_model_lstm_Cons_3 = this.x_model_lstm_Cons_3;
            onnxParams.Learnables.x_model_lstm_Cons_4 = this.x_model_lstm_Cons_4;
            onnxParams.Learnables.x_model_lstm_Cons_5 = this.x_model_lstm_Cons_5;
            [x_model_lstm_Squeeze, x_model_lstm_Expa_3, x_model_lstm_Expa_4, x_model_lstm_SqueezeNumDims, x_model_lstm_Expa_3NumDims, x_model_lstm_Expa_4NumDims] = Squeeze_To_ExpandFcn(x_model_lstm_LSTM_1_, x_model_lstm_LSTM_1_NumDims, onnxParams, 'Training', true, ...
                'InputDataPermutation', {[3 4 2 1], ['as-is']}, ...
                'OutputDataPermutation', {[3 2 1], [3 2 1], [3 2 1], ['as-is'], ['as-is'], ['as-is']});
            if any(cellfun(@(A)~isnumeric(A), {x_model_lstm_Squeeze, x_model_lstm_Expa_3, x_model_lstm_Expa_4}))
                fprintf('Runtime error in network. The custom layer ''%s'' output a non-numeric value.\n', 'Squeeze_To_ExpandLayer1019');
                error(message('nnet_cnn_onnx:onnx:BadCustomLayerRuntimeOutput', 'Squeeze_To_ExpandLayer1019'));
            end
            x_model_lstm_Squeeze = dlarray(single(x_model_lstm_Squeeze), 'CBT');
            x_model_lstm_Expa_3 = dlarray(single(x_model_lstm_Expa_3), 'CB');
            x_model_lstm_Expa_4 = dlarray(single(x_model_lstm_Expa_4), 'CB');
            if ~coder.target('MATLAB')
                x_model_lstm_Squeeze = extractdata(x_model_lstm_Squeeze);
                x_model_lstm_Expa_3 = extractdata(x_model_lstm_Expa_3);
                x_model_lstm_Expa_4 = extractdata(x_model_lstm_Expa_4);
            end
        end
    end
end

function [x_model_lstm_Squeeze, x_model_lstm_Expa_3, x_model_lstm_Expa_4, x_model_lstm_SqueezeNumDims, x_model_lstm_Expa_3NumDims, x_model_lstm_Expa_4NumDims, state] = Squeeze_To_ExpandFcn(x_model_lstm_LSTM_1_, x_model_lstm_LSTM_1_NumDims, params, varargin)
%SQUEEZE_TO_EXPANDFCN Function implementing an imported ONNX network.
%
% THIS FILE WAS AUTO-GENERATED BY importONNXFunction.
% ONNX Operator Set Version: 14
%
% Variable names in this function are taken from the original ONNX file.
%
% [X_MODEL_LSTM_SQUEEZE, X_MODEL_LSTM_EXPA_3, X_MODEL_LSTM_EXPA_4] = Squeeze_To_ExpandFcn(X_MODEL_LSTM_LSTM_1_, PARAMS)
%			- Evaluates the imported ONNX network SQUEEZE_TO_EXPANDFCN with input(s)
%			X_MODEL_LSTM_LSTM_1_ and the imported network parameters in PARAMS. Returns
%			network output(s) in X_MODEL_LSTM_SQUEEZE, X_MODEL_LSTM_EXPA_3, X_MODEL_LSTM_EXPA_4.
%
% [X_MODEL_LSTM_SQUEEZE, X_MODEL_LSTM_EXPA_3, X_MODEL_LSTM_EXPA_4, STATE] = Squeeze_To_ExpandFcn(X_MODEL_LSTM_LSTM_1_, PARAMS)
%			- Additionally returns state variables in STATE. When training,
%			use this form and set TRAINING to true.
%
% [__] = Squeeze_To_ExpandFcn(X_MODEL_LSTM_LSTM_1_, PARAMS, 'NAME1', VAL1, 'NAME2', VAL2, ...)
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
% X_MODEL_LSTM_LSTM_1_
%			- Input(s) to the ONNX network.
%			  The input size(s) expected by the ONNX file are:
%				  X_MODEL_LSTM_LSTM_1_:		[Unknown, Unknown, Unknown, Unknown]				Type: FLOAT
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
% X_MODEL_LSTM_SQUEEZE, X_MODEL_LSTM_EXPA_3, X_MODEL_LSTM_EXPA_4
%			- Output(s) of the ONNX network.
%			  Without permutation, the size(s) of the outputs are:
%				  X_MODEL_LSTM_SQUEEZE:		[Unknown, Unknown, Unknown]				Type: FLOAT
%				  X_MODEL_LSTM_EXPA_3:		[Unknown, Unknown, Unknown]				Type: FLOAT
%				  X_MODEL_LSTM_EXPA_4:		[Unknown, Unknown, Unknown]				Type: FLOAT
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
[x_model_lstm_LSTM_1_, Training, outputDataPerms, anyDlarrayInputs] = preprocessInput(x_model_lstm_LSTM_1_, params, varargin{:});
% Put all variables into a single struct to implement dynamic scoping:
[Vars, NumDims] = packageVariables(params, {'x_model_lstm_LSTM_1_'}, {x_model_lstm_LSTM_1_}, [x_model_lstm_LSTM_1_NumDims]);
% Call the top-level graph function:
[x_model_lstm_Squeeze, x_model_lstm_Expa_3, x_model_lstm_Expa_4, x_model_lstm_SqueezeNumDims, x_model_lstm_Expa_3NumDims, x_model_lstm_Expa_4NumDims, state] = Squeeze_To_ExpandGraph1014(x_model_lstm_LSTM_1_, NumDims.x_model_lstm_LSTM_1_, Vars, NumDims, Training, params.State);
% Postprocess the output data
[x_model_lstm_Squeeze, x_model_lstm_Expa_3, x_model_lstm_Expa_4] = postprocessOutput(x_model_lstm_Squeeze, x_model_lstm_Expa_3, x_model_lstm_Expa_4, outputDataPerms, anyDlarrayInputs, Training, varargin{:});
end

function [x_model_lstm_Squeeze, x_model_lstm_Expa_3, x_model_lstm_Expa_4, x_model_lstm_SqueezeNumDims1016, x_model_lstm_Expa_3NumDims1017, x_model_lstm_Expa_4NumDims1018, state] = Squeeze_To_ExpandGraph1014(x_model_lstm_LSTM_1_, x_model_lstm_LSTM_1_NumDims1015, Vars, NumDims, Training, state)
% Function implementing the graph 'Squeeze_To_ExpandGraph1014'
% Update Vars and NumDims from the graph's formal input parameters. Note that state variables are already in Vars.
Vars.x_model_lstm_LSTM_1_ = x_model_lstm_LSTM_1_;
NumDims.x_model_lstm_LSTM_1_ = x_model_lstm_LSTM_1_NumDims1015;

% Execute the operators:
% Squeeze:
[Vars.x_model_lstm_Squeeze, NumDims.x_model_lstm_Squeeze] = onnxSqueeze(Vars.x_model_lstm_LSTM_1_, Vars.x_model_lstm_Cons_3, NumDims.x_model_lstm_LSTM_1_);

% Shape:
[Vars.x_model_lstm_Shape_4, NumDims.x_model_lstm_Shape_4] = onnxShape(Vars.x_model_lstm_Squeeze, NumDims.x_model_lstm_Squeeze);

% Gather:
[Vars.x_model_lstm_Gath_3, NumDims.x_model_lstm_Gath_3] = onnxGather(Vars.x_model_lstm_Shape_4, Vars.x_model_lstm_Cons_6, 0, NumDims.x_model_lstm_Shape_4, NumDims.x_model_lstm_Cons_6);

% Unsqueeze:
[shape, NumDims.onnx__Concat_283] = prepareUnsqueezeArgs(Vars.x_model_lstm_Gath_3, Vars.onnx__Unsqueeze_282, NumDims.x_model_lstm_Gath_3);
Vars.onnx__Concat_283 = reshape(Vars.x_model_lstm_Gath_3, shape);

% Concat:
[Vars.x_model_lstm_Conc_3, NumDims.x_model_lstm_Conc_3] = onnxConcat(0, {Vars.onnx__Concat_403, Vars.onnx__Concat_283, Vars.x_model_lstm_Cons_7}, [NumDims.onnx__Concat_403, NumDims.onnx__Concat_283, NumDims.x_model_lstm_Cons_7]);

% Expand:
[shape, NumDims.x_model_lstm_Expa_3] = prepareExpandArgs(Vars.x_model_lstm_Conc_3);
Vars.x_model_lstm_Expa_3 = Vars.x_model_lstm_Cons_4 + zeros(shape);

% Shape:
[Vars.x_model_lstm_Shape_5, NumDims.x_model_lstm_Shape_5] = onnxShape(Vars.x_model_lstm_Squeeze, NumDims.x_model_lstm_Squeeze);

% Gather:
[Vars.x_model_lstm_Gath_4, NumDims.x_model_lstm_Gath_4] = onnxGather(Vars.x_model_lstm_Shape_5, Vars.x_model_lstm_Cons_8, 0, NumDims.x_model_lstm_Shape_5, NumDims.x_model_lstm_Cons_8);

% Unsqueeze:
[shape, NumDims.onnx__Concat_294] = prepareUnsqueezeArgs(Vars.x_model_lstm_Gath_4, Vars.onnx__Unsqueeze_293, NumDims.x_model_lstm_Gath_4);
Vars.onnx__Concat_294 = reshape(Vars.x_model_lstm_Gath_4, shape);

% Concat:
[Vars.x_model_lstm_Conc_4, NumDims.x_model_lstm_Conc_4] = onnxConcat(0, {Vars.onnx__Concat_404, Vars.onnx__Concat_294, Vars.x_model_lstm_Cons_9}, [NumDims.onnx__Concat_404, NumDims.onnx__Concat_294, NumDims.x_model_lstm_Cons_9]);

% Expand:
[shape, NumDims.x_model_lstm_Expa_4] = prepareExpandArgs(Vars.x_model_lstm_Conc_4);
Vars.x_model_lstm_Expa_4 = Vars.x_model_lstm_Cons_5 + zeros(shape);

% Set graph output arguments from Vars and NumDims:
x_model_lstm_Squeeze = Vars.x_model_lstm_Squeeze;
x_model_lstm_SqueezeNumDims1016 = NumDims.x_model_lstm_Squeeze;
x_model_lstm_Expa_3 = Vars.x_model_lstm_Expa_3;
x_model_lstm_Expa_3NumDims1017 = NumDims.x_model_lstm_Expa_3;
x_model_lstm_Expa_4 = Vars.x_model_lstm_Expa_4;
x_model_lstm_Expa_4NumDims1018 = NumDims.x_model_lstm_Expa_4;
% Set output state from Vars:
state = updateStruct(state, Vars);
end

function [inputDataPerms, outputDataPerms, Training] = parseInputs(x_model_lstm_LSTM_1_, numDataOutputs, params, varargin)
% Function to validate inputs to Squeeze_To_ExpandFcn:
p = inputParser;
isValidArrayInput = @(x)isnumeric(x) || isstring(x);
isValidONNXParameters = @(x)isa(x, 'ONNXParameters');
addRequired(p, 'x_model_lstm_LSTM_1_', isValidArrayInput);
addRequired(p, 'params', isValidONNXParameters);
addParameter(p, 'InputDataPermutation', 'auto');
addParameter(p, 'OutputDataPermutation', 'auto');
addParameter(p, 'Training', false);
parse(p, x_model_lstm_LSTM_1_, params, varargin{:});
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

function [x_model_lstm_LSTM_1_, Training, outputDataPerms, anyDlarrayInputs] = preprocessInput(x_model_lstm_LSTM_1_, params, varargin)
% Parse input arguments
[inputDataPerms, outputDataPerms, Training] = parseInputs(x_model_lstm_LSTM_1_, 3, params, varargin{:});
anyDlarrayInputs = any(cellfun(@(x)isa(x, 'dlarray'), {x_model_lstm_LSTM_1_}));
% Make the input variables into unlabelled dlarrays:
x_model_lstm_LSTM_1_ = makeUnlabeledDlarray(x_model_lstm_LSTM_1_);
% Permute inputs if requested:
x_model_lstm_LSTM_1_ = permuteInputVar(x_model_lstm_LSTM_1_, inputDataPerms{1}, 4);
end

function [x_model_lstm_Squeeze, x_model_lstm_Expa_3, x_model_lstm_Expa_4] = postprocessOutput(x_model_lstm_Squeeze, x_model_lstm_Expa_3, x_model_lstm_Expa_4, outputDataPerms, anyDlarrayInputs, Training, varargin)
% Set output type:
if ~anyDlarrayInputs && ~Training
    if isdlarray(x_model_lstm_Squeeze)
        x_model_lstm_Squeeze = extractdata(x_model_lstm_Squeeze);
    end
    if isdlarray(x_model_lstm_Expa_3)
        x_model_lstm_Expa_3 = extractdata(x_model_lstm_Expa_3);
    end
    if isdlarray(x_model_lstm_Expa_4)
        x_model_lstm_Expa_4 = extractdata(x_model_lstm_Expa_4);
    end
end
% Permute outputs if requested:
x_model_lstm_Squeeze = permuteOutputVar(x_model_lstm_Squeeze, outputDataPerms{1}, 3);
x_model_lstm_Expa_3 = permuteOutputVar(x_model_lstm_Expa_3, outputDataPerms{2}, 3);
x_model_lstm_Expa_4 = permuteOutputVar(x_model_lstm_Expa_4, outputDataPerms{3}, 3);
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

function [shape, numDimsY] = prepareExpandArgs(ONNXShape)
% Prepares arguments for implementing the ONNX Expand operator

% Broadcast X to ONNXShape. The shape of X must be compatible with ONNXShape.
ONNXShape = extractdata(ONNXShape);
shape = fliplr(ONNXShape(:)');
if numel(shape) < 2
    shape = [shape ones(1, 2-numel(shape))];
end
numDimsY = numel(ONNXShape);
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
