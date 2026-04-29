
import torch

from dataset_generator import generate_dataset
from game.ai_nn import TacticsNet, train, TacticsDataset, DataLoader


generate_dataset(num_games=200, depth=2)




samples = torch.load("tactics_dataset.pt")
dataset = TacticsDataset(samples)
loader = DataLoader(dataset, batch_size=64, shuffle=True)

model = TacticsNet(height=8, width=8, channels=14, max_units=8)
train(model, loader, epochs=20)
