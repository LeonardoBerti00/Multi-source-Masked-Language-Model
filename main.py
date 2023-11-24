from pathlib import Path

import wandb
from lightning.pytorch.loggers import WandbLogger
from run import run_wandb, run, sweep_init
import torch
import constants as cst
from config import Configuration
from models.LitModel import LitModel


def set_torch():
    #torch.manual_seed(cst.SEED)
    torch.set_default_dtype(torch.float32)
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    torch.autograd.set_detect_anomaly(True)
    torch.set_float32_matmul_precision('high')

if __name__ == "__main__":
    set_torch()
    torch.autograd.set_detect_anomaly(True)
    config = Configuration()
    if cst.DEVICE == "cpu":
        accelerator = "cpu"
    else:
        accelerator = "gpu"


    if config.IS_WANDB:
        wandb_logger = WandbLogger(project=cst.PROJECT_NAME, log_model="all", save_dir=cst.DIR_SAVED_MODEL)
        if config.IS_SWEEP:
            sweep_config = sweep_init(config)
            sweep_config.update({"name": f"model_{config.CHOSEN_MODEL.name}"})
            sweep_id = wandb.sweep(sweep_config, project=cst.PROJECT_NAME)
            wandb.agent(sweep_id, run_wandb(config, accelerator, wandb_logger), count=sweep_config["run_cap"])
        else:
            start_wandb = run_wandb(config, accelerator, wandb_logger)
            start_wandb()

    elif config.IS_TESTING:
        dir = Path(cst.DIR_SAVED_MODEL + "/" + str(config.CHOSEN_MODEL.name))
        best_val_loss = 100000

        for file in dir.iterdir():
            val_loss = float(file.name.split("=")[1].split("_")[0])
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                checkpoint_reference = file

        # load checkpoint
        model = LitModel.load_from_checkpoint(checkpoint_reference)
        run(config, accelerator, model)

    # training without using wandb
    elif config.IS_TRAINING:
        run(config, accelerator)