import logging
import torch
import torch.nn as nn
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor

logger = logging.getLogger(__name__)


class BombermanCNN(BaseFeaturesExtractor):
    """
    Custom CNN feature extractor for Bomberman grid observations.
    
    Handles 5-channel grid input (terrain, player, enemies, weapons, powerups).
    Architecture inspired by NatureCNN but adapted for 5-channel input.
    
    The CNN processes spatial grid data through convolutional layers,
    extracting spatial features that are important for game strategy.
    """
    
    def __init__(
        self,
        observation_space,
        features_dim: int = 512,
    ) -> None:
        """
        Initialize CNN feature extractor for grid observations.
        
        Args:
            observation_space: Gymnasium observation space for grid data.
                Expected shape: (GRID_CHANNELS, WINDOW_SIZE, WINDOW_SIZE)
            features_dim: Dimension of the output feature vector after CNN processing.
        """
        super().__init__(observation_space, features_dim)
        
        # Get number of input channels from observation space
        # Expected shape: (channels, height, width) = (5, 15, 15) or (5, 7, 7) or similar
        n_input_channels: int = observation_space.shape[0]
        input_height: int = observation_space.shape[1]
        input_width: int = observation_space.shape[2]
        
        logger.info(
            f"BombermanCNN initialized: input_shape={observation_space.shape}, "
            f"features_dim={features_dim}"
        )
        
        # Adaptive CNN architecture based on input size
        # For small inputs (7x7), use smaller kernels and fewer layers
        # For larger inputs (15x15), use standard architecture
        if input_height <= 7 or input_width <= 7:
            # Small input architecture (e.g., 7x7)
            logger.info("Using small input CNN architecture (for 7x7 or smaller)")
            self.cnn = nn.Sequential(
                # First conv layer: small kernel for small inputs
                nn.Conv2d(
                    in_channels=n_input_channels,
                    out_channels=32,
                    kernel_size=3,
                    stride=1,
                    padding=1,  # Use padding to preserve size
                ),
                nn.ReLU(),
                # Second conv layer: small kernel
                nn.Conv2d(
                    in_channels=32,
                    out_channels=64,
                    kernel_size=3,
                    stride=1,
                    padding=1,
                ),
                nn.ReLU(),
                # Adaptive pooling to fixed size before flattening
                nn.AdaptiveAvgPool2d(output_size=(2, 2)),  # Fixed output size
                nn.Flatten(),
            )
            # Calculate flattened size: 64 channels * 2 * 2 = 256
            n_flatten = 64 * 2 * 2
        else:
            # Standard architecture for larger inputs (15x15 or larger)
            logger.info("Using standard CNN architecture (for 15x15 or larger)")
            # Use smaller kernels and strides to avoid size issues
            # For 15x15: 
            # - Conv1: kernel=5, stride=2, padding=1 -> (15+2-5)/2+1 = 7x7
            # - Conv2: kernel=3, stride=2, padding=1 -> (7+2-3)/2+1 = 4x4
            # - Conv3: kernel=3, stride=1, padding=1 -> 4x4
            # - Adaptive pooling to 2x2 -> 2x2
            self.cnn = nn.Sequential(
                # First conv layer: medium kernel with stride 2
                # Input: (batch, 5, 15, 15) -> Output: (batch, 32, 7, 7)
                nn.Conv2d(
                    in_channels=n_input_channels,
                    out_channels=32,
                    kernel_size=5,
                    stride=2,
                    padding=1,
                ),
                nn.ReLU(),
                # Second conv layer: small kernel with stride 2
                # Input: (batch, 32, 7, 7) -> Output: (batch, 64, 4, 4)
                nn.Conv2d(
                    in_channels=32,
                    out_channels=64,
                    kernel_size=3,
                    stride=2,
                    padding=1,
                ),
                nn.ReLU(),
                # Third conv layer: small kernel to extract features
                # Input: (batch, 64, 4, 4) -> Output: (batch, 64, 4, 4)
                nn.Conv2d(
                    in_channels=64,
                    out_channels=64,
                    kernel_size=3,
                    stride=1,
                    padding=1,
                ),
                nn.ReLU(),
                # Adaptive pooling to fixed size for consistent output
                nn.AdaptiveAvgPool2d(output_size=(2, 2)),
                nn.Flatten(),
            )
            
            # Calculate the output size after conv layers dynamically
            # This is needed to determine the input size for the linear layer
            with torch.no_grad():
                dummy_input = torch.zeros(1, n_input_channels, input_height, input_width)
                cnn_output = self.cnn(dummy_input)
                n_flatten: int = cnn_output.shape[1]


        
        logger.info(
            f"CNN output size after conv layers: {n_flatten} "
            f"(input: {n_input_channels}x{input_height}x{input_width})"
        )
        
        # Linear layer to map CNN output to desired feature dimension
        self.linear = nn.Sequential(
            nn.Linear(n_flatten, features_dim),
            nn.ReLU(),
        )
    
    def forward(self, observations: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through CNN feature extractor.
        
        Args:
            observations: Input tensor of shape (batch, channels, height, width)
                or (channels, height, width) for single observation.
        
        Returns:
            Feature vector of shape (batch, features_dim) or (features_dim,).
        """
        # Process through CNN layers
        cnn_features = self.cnn(observations)
        # Map to final feature dimension
        features = self.linear(cnn_features)
        return features


class BombermanCombinedFeatureExtractor(BaseFeaturesExtractor):
    """
    Combined feature extractor for Bomberman observations with both grid and stats.
    
    This extractor processes:
    - Grid data (spatial) through CNN
    - Stats data (vector) through MLP
    - Combines both into a single feature vector
    
    This is designed to work with MultiInputLstmPolicy which expects
    a single feature extractor that can handle dict observations.
    """
    
    def __init__(
        self,
        observation_space,
        features_dim: int = 512,
        cnn_features_dim: int = 256,
        mlp_features_dim: int = 64,
    ) -> None:
        """
        Initialize combined feature extractor.
        
        Args:
            observation_space: Gymnasium Dict observation space with 'grid' and 'stats' keys.
            features_dim: Final output feature dimension.
            cnn_features_dim: Feature dimension for CNN output (grid processing).
            mlp_features_dim: Feature dimension for MLP output (stats processing).
        """
        super().__init__(observation_space, features_dim)
        
        # Extract grid and stats spaces
        grid_space = observation_space.spaces["grid"]
        stats_space = observation_space.spaces["stats"]
        
        logger.info(
            f"BombermanCombinedFeatureExtractor initialized: "
            f"grid_shape={grid_space.shape}, stats_shape={stats_space.shape}, "
            f"features_dim={features_dim}"
        )
        
        # CNN for grid data
        self.cnn_extractor = BombermanCNN(
            observation_space=grid_space,
            features_dim=cnn_features_dim,
        )
        
        # MLP for stats data
        stats_dim: int = stats_space.shape[0]
        self.mlp = nn.Sequential(
            nn.Linear(stats_dim, mlp_features_dim),
            nn.ReLU(),
            nn.Linear(mlp_features_dim, mlp_features_dim),
            nn.ReLU(),
        )
        
        # Combine CNN and MLP features
        combined_dim = cnn_features_dim + mlp_features_dim
        self.combiner = nn.Sequential(
            nn.Linear(combined_dim, features_dim),
            nn.ReLU(),
        )
    
    def forward(self, observations: dict[str, torch.Tensor]) -> torch.Tensor:
        """
        Forward pass through combined feature extractor.
        
        Args:
            observations: Dict with 'grid' and 'stats' keys.
                - 'grid': (batch, channels, height, width) or (channels, height, width)
                - 'stats': (batch, stats_dim) or (stats_dim,)
        
        Returns:
            Combined feature vector of shape (batch, features_dim) or (features_dim,).
        """
        # Process grid through CNN
        grid_features = self.cnn_extractor(observations["grid"])
        
        # Process stats through MLP
        stats_features = self.mlp(observations["stats"])
        
        # Combine features
        combined = torch.cat([grid_features, stats_features], dim=-1)
        
        # Map to final feature dimension
        features = self.combiner(combined)
        return features

