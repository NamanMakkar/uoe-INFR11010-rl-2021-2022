from abc import ABC, abstractmethod
from copy import deepcopy
import gym
import numpy as np
import os.path
from torch import Tensor
from torch.distributions.categorical import Categorical
import torch.nn
from torch.optim import Adam
from typing import Dict, Iterable, List

from rl2022.exercise3.networks import FCNetwork
from rl2022.exercise3.replay import Transition


class Agent(ABC):
    """Base class for Deep RL Exercise 3 Agents
    **DO NOT CHANGE THIS CLASS**
    :attr action_space (gym.Space): action space of used environment
    :attr observation_space (gym.Space): observation space of used environment
    :attr saveables (Dict[str, torch.nn.Module]):
        mapping from network names to PyTorch network modules
    Note:
        see http://gym.openai.com/docs/#spaces for more information on Gym spaces
    """

    def __init__(self, action_space: gym.Space, observation_space: gym.Space):
        """The constructor of the Agent Class
        :param action_space (gym.Space): environment's action space
        :param observation_space (gym.Space): environment's observation space
        """
        self.action_space = action_space
        self.observation_space = observation_space

        self.saveables = {}

    def save(self, path: str, suffix: str = "") -> str:
        """Saves saveable PyTorch models under given path
        The models will be saved in directory found under given path in file "models_{suffix}.pt"
        where suffix is given by the optional parameter (by default empty string "")
        :param path (str): path to directory where to save models
        :param suffix (str, optional): suffix given to models file
        :return (str): path to file of saved models file
        """
        torch.save(self.saveables, path)
        return path

    def restore(self, save_path: str):
        """Restores PyTorch models from models file given by path
        :param save_path (str): path to file containing saved models
        """
        dirname, _ = os.path.split(os.path.abspath(__file__))
        save_path = os.path.join(dirname, save_path)
        checkpoint = torch.load(save_path)
        for k, v in self.saveables.items():
            v.load_state_dict(checkpoint[k].state_dict())

    @abstractmethod
    def act(self, obs: np.ndarray):
        ...

    @abstractmethod
    def schedule_hyperparameters(self, timestep: int, max_timestep: int):
        """Updates the hyperparameters
        This function is called before every episode and allows you to schedule your
        hyperparameters.
        :param timestep (int): current timestep at the beginning of the episode
        :param max_timestep (int): maximum timesteps that the training loop will run for
        """
        ...

    @abstractmethod
    def update(self):
        ...


class DQN(Agent):
    """DQN agent
    **YOU NEED TO IMPLEMENT FUNCTIONS IN THIS CLASS**
    :attr critics_net (FCNetwork): fully connected DQN to compute Q-value estimates
    :attr critics_target (FCNetwork): fully connected DQN target network
    :attr critics_optim (torch.optim): PyTorch optimiser for DQN critics_net
    :attr learning_rate (float): learning rate for DQN optimisation
    :attr update_counter (int): counter of updates for target network updates
    :attr target_update_freq (int): update frequency (number of iterations after which the target
        networks should be updated)
    :attr batch_size (int): size of sampled batches of experience
    :attr gamma (float): discount rate gamma
    """

    def __init__(
        self,
        action_space: gym.Space,
        observation_space: gym.Space,
        learning_rate: float,
        hidden_size: Iterable[int],
        target_update_freq: int,
        batch_size: int,
        gamma: float,
        **kwargs,
    ):
        """The constructor of the DQN agent class
        **YOU MUST IMPLEMENT THIS FUNCTION FOR Q3**
        :param action_space (gym.Space): environment's action space
        :param observation_space (gym.Space): environment's observation space
        :param learning_rate (float): learning rate for DQN optimisation
        :param hidden_size (Iterable[int]): list of hidden dimensionalities for fully connected DQNs
        :param target_update_freq (int): update frequency (number of iterations after which the target
            networks should be updated)
        :param batch_size (int): size of sampled batches of experience
        :param gamma (float): discount rate gamma
        """
        super().__init__(action_space, observation_space)

        STATE_SIZE = observation_space.shape[0]
        ACTION_SIZE = action_space.n

        # ######################################### #
        #  BUILD YOUR NETWORKS AND OPTIMIZERS HERE  #
        # ######################################### #
        self.critics_net = FCNetwork(
            (STATE_SIZE, *hidden_size, ACTION_SIZE), output_activation=None
        )

        self.critics_target = deepcopy(self.critics_net)

        self.critics_optim = Adam(
            self.critics_net.parameters(), lr=learning_rate, eps=1e-3
        )

        # ############################################# #
        # WRITE ANY HYPERPARAMETERS YOU MIGHT NEED HERE #
        # ############################################# #
        self.learning_rate = learning_rate
        self.update_counter = 0
        self.target_update_freq = target_update_freq
        self.batch_size = batch_size
        self.gamma = gamma

        self.epsilon = 1
        # ######################################### #
        self.saveables.update(
            {
                "critics_net": self.critics_net,
                "critics_target": self.critics_target,
                "critic_optim": self.critics_optim,
            }
        )

    def schedule_hyperparameters(self, timestep: int, max_timestep: int):
        """Updates the hyperparameters
        **YOU MUST IMPLEMENT THIS FUNCTION FOR Q3**
        This function is called before every episode and allows you to schedule your
        hyperparameters.
        :param timestep (int): current timestep at the beginning of the episode
        :param max_timestep (int): maximum timesteps that the training loop will run for
        """
        self.epsilon = self.epsilon / 1.007

    def act(self, obs: np.ndarray, explore: bool):
        """Returns an action (should be called at every timestep)
        **YOU MUST IMPLEMENT THIS FUNCTION FOR Q3**
        When explore is False you should select the best action possible (greedy). However, during
        exploration, you should be implementing an exploration strategy (like e-greedy). Use
        schedule_hyperparameters() for any hyperparameters that you want to change over time.
        :param obs (np.ndarray): observation vector from the environment
        :param explore (bool): flag indicating whether we should explore
        :return (sample from self.action_space): action the agent should perform
        """
        state = torch.from_numpy(np.array([obs])).float()
        q_state = self.critics_net(state).detach().numpy()
        if explore:
            uniform_dist = np.random.uniform(low=0.0,high=1.0,size=1)
            random_action = np.random.choice(q_state.size)

            if uniform_dist < self.epsilon:
                return random_action
        
        return np.argmax(q_state)

    def update(self, batch: Transition) -> Dict[str, float]:
        """Update function for DQN
        **YOU MUST IMPLEMENT THIS FUNCTION FOR Q3**
        This function is called after storing a transition in the replay buffer. This happens
        every timestep. It should update your network, update the target network at the given
        target update frequency, and return the Q-loss in the form of a dictionary.
        :param batch (Transition): batch vector from replay buffer
        :return (Dict[str, float]): dictionary mapping from loss names to loss values
        """
        ### PUT YOUR CODE HERE ###

        q_loss = 0.0
        self.critics_optim.zero_grad()
        criterion = torch.nn.MSELoss()
        states = getattr(batch, 'states')
        actions = getattr(batch, 'actions')
        rewards = getattr(batch, 'rewards')
        next_states = getattr(batch, 'next_states')
        done = getattr(batch, 'done')
        max_qs = self.critics_target(next_states).max(1)[0].detach().unsqueeze(1)
        y = rewards + (1 - done) * self.gamma * max_qs
        target = self.critics_net(states).gather(dim=1, index=actions.long())
        q_loss = criterion(y, target)
        q_loss.backward()
        self.critics_optim.step()
        self.update_counter += 1
        if self.update_counter % self.target_update_freq == 0:
            self.critics_target.hard_update(self.critics_net)
        return {"q_loss": q_loss.detach().numpy()}

class Reinforce(Agent):
    """Reinforce agent
    **YOU NEED TO IMPLEMENT FUNCTIONS IN THIS CLASS**
    :attr policy (FCNetwork): fully connected network for policy
    :attr policy_optim (torch.optim): PyTorch optimiser for policy network
    :attr learning_rate (float): learning rate for DQN optimisation
    :attr gamma (float): discount rate gamma
    """

    def __init__(
        self,
        action_space: gym.Space,
        observation_space: gym.Space,
        learning_rate: float,
        hidden_size: Iterable[int],
        gamma: float,
        **kwargs,
    ):
        """
        **YOU MUST IMPLEMENT THIS FUNCTION FOR Q3**
        :param action_space (gym.Space): environment's action space
        :param observation_space (gym.Space): environment's observation space
        :param learning_rate (float): learning rate for DQN optimisation
        :param hidden_size (Iterable[int]): list of hidden dimensionalities for fully connected DQNs
        :param gamma (float): discount rate gamma
        """
        super().__init__(action_space, observation_space)
        STATE_SIZE = observation_space.shape[0]
        ACTION_SIZE = action_space.n

        # ######################################### #
        #  BUILD YOUR NETWORKS AND OPTIMIZERS HERE  #
        # ######################################### #
        self.policy = FCNetwork(
            (STATE_SIZE, *hidden_size, ACTION_SIZE), output_activation=torch.nn.modules.activation.Softmax
        )

        self.policy_optim = Adam(self.policy.parameters(), lr=learning_rate, eps=1e-3)

        # ############################################# #
        # WRITE ANY HYPERPARAMETERS YOU MIGHT NEED HERE #
        # ############################################# #
        self.learning_rate = learning_rate
        self.gamma = gamma

        # ############################### #
        # WRITE ANY AGENT PARAMETERS HERE #
        # ############################### #

        # ###############################################
        self.saveables.update(
            {
                "policy": self.policy,
            }
        )

    def schedule_hyperparameters(self, timestep: int, max_timesteps: int):
        """Updates the hyperparameters 
        **YOU MUST IMPLEMENT THIS FUNCTION FOR Q3**
        This function is called before every episode and allows you to schedule your
        hyperparameters.
        :param timestep (int): current timestep at the beginning of the episode
        :param max_timestep (int): maximum timesteps that the training loop will run for
        """
        ### PUT YOUR CODE HERE ###
        self.learning_rate = self.learning_rate / 1.009
        self.gamma = min(0.999999999, self.gamma * 1.000000001)

    def act(self, obs: np.ndarray, explore: bool):
        """Returns an action (should be called at every timestep)
        **YOU MUST IMPLEMENT THIS FUNCTION FOR Q3**
        Select an action from the model's stochastic policy by sampling a discrete action
        from the distribution specified by the model output
        :param obs (np.ndarray): observation vector from the environment
        :param explore (bool): flag indicating whether we should explore
        :return (sample from self.action_space): action the agent should perform
        """
        self.action_probs = self.policy.forward(torch.from_numpy(obs).float()).detach().numpy()
        
        if explore:
            action = np.random.choice(np.arange(len(self.action_probs)), p = self.action_probs)
            return action       
        return np.argmax(self.action_probs)

    def update(
        self, rewards: List[float], observations: List[np.ndarray], actions: List[int],
        ) -> Dict[str, float]:
        """Update function for policy gradients
        **YOU MUST IMPLEMENT THIS FUNCTION FOR Q3**
        :param rewards (List[float]): rewards of episode (from first to last)
        :param observations (List[np.ndarray]): observations of episode (from first to last)
        :param actions (List[int]): applied actions of episode (from first to last)
        :return (Dict[str, float]): dictionary mapping from loss names to loss values
            losses
        """
        ### PUT YOUR CODE HERE ###
        p_loss = 0.0
        self.policy.train()
        G = 0
        T = len(actions)
        for t in range(T-1,-1,-1):
            G = rewards[t] + self.gamma*G
            action_probs = self.policy.forward(torch.from_numpy(observations[t]).float())
            p_loss -= G * torch.log(action_probs[t])
        
        p_loss = p_loss / T

        self.policy_optim.zero_grad()
        p_loss.backward()
        self.policy_optim.step()
        return {"p_loss": p_loss.detach().numpy()}