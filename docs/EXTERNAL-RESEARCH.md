# External Research Register — Initial

External projects are research references only until license and integration decisions are explicitly documented.

## High-priority references

### NAM-EQ-Match

Relevance:
- demonstrates a practical combination of non-spectral guitar descriptors and EQ matching;
- useful for feature-selection ideas and baseline comparison;
- NAM-library selection is conceptually different from the intended direct 125A transformation.

125A intent:
- study methodology and measurable descriptors;
- do not assume its architecture is the product architecture.

### DeepAFx / DeepAFx-ST research

Relevance:
- reference/style-conditioned control of structured audio effects;
- supports the idea of ML predicting parameters of interpretable DSP rather than generating waveform output directly.

125A intent:
- research the primary papers and exact license before any implementation borrowing;
- independently implement any adopted concepts.

### DDSP / timbre-transfer literature

Relevance:
- separates performance-related descriptors from timbral resynthesis;
- useful as a comparison against structured DSP tone transfer.

125A intent:
- research only unless a concrete advantage for distorted guitar is demonstrated.

### GuitarLSTM / neural amp modelling

Relevance:
- demonstrates learned nonlinear guitar-device behaviour from paired input/output data.

Limitation for this project:
- requires a different problem formulation than unpaired reference tone matching;
- primarily useful as a contrast case and possible future nonlinear submodule research.

### RTNeural / NeuralAmpModelerCore

Relevance:
- realtime neural inference architecture and performance methodology.

125A intent:
- relevant only if a neural component earns its place experimentally.

## License boundary

Before using any external code or model:

1. verify exact repository and revision;
2. verify license;
3. verify dependency licenses;
4. determine whether source reuse is compatible with the intended product;
5. otherwise treat the project as research-only and independently derive the implementation from primary technical sources.

GPL or otherwise incompatible code is not copied into a closed 125A product without explicit licensing/legal review.
