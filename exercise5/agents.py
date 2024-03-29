from abc import ABC, abstractmethod
from collections import defaultdict
import random
from copy import deepcopy
from typing import List, Dict, DefaultDict
import numpy as np

from gym.spaces import Space
from gym.spaces.utils import flatdim


class MultiAgent(ABC):
    """Base class for multi-agent reinforcement learning
    **DO NOT CHANGE THIS BASE CLASS**
    """

    def __init__(
        self,
        num_agents: int,
        action_spaces: List[Space],
        gamma: float,
        **kwargs
    ):
        """Constructor of base agent for Q-Learning
        Initializes basic variables of MARL agents
        namely epsilon, learning rate and discount rate.
        :param num_agents (int): number of agents
        :param action_spaces (List[Space]): action spaces of the environment for each agent
        :param gamma (float): discount factor (gamma)
        :attr n_acts (List[int]): number of actions for each agent
        """

        self.num_agents = num_agents
        self.action_spaces = action_spaces
        self.n_acts = [flatdim(action_space) for action_space in action_spaces]

        self.gamma: float = gamma

    @abstractmethod
    def act(self) -> List[int]:
        """Chooses an action for all agents for stateless task
        :return (List[int]): index of selected action for each agent
        """
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
    def learn(self):
        ...


class IndependentQLearningAgents(MultiAgent):
    """Agent using the Independent Q-Learning algorithm
    **YOU NEED TO IMPLEMENT FUNCTIONS IN THIS CLASS**
    """

    def __init__(self, learning_rate: float =0.5, epsilon: float =1.0, **kwargs):
        """Constructor of IndependentQLearningAgents
        :param learning_rate (float): learning rate for Q-learning updates
        :param epsilon (float): epsilon value for all agents
        :attr q_tables (List[DefaultDict]): tables for Q-values mapping actions ACTs
            to respective Q-values for all agents
        Initializes some variables of the Independent Q-Learning agents, namely the epsilon, discount rate
        and learning rate
        """

        super().__init__(**kwargs)
        self.learning_rate = learning_rate
        self.epsilon = epsilon

        # initialise Q-tables for all agents
        self.q_tables: List[DefaultDict] = [defaultdict(lambda: 0) for i in range(self.num_agents)]


    def act(self) -> List[int]:
        """Implement the epsilon-greedy action selection here for stateless task
        **YOU MUST IMPLEMENT THIS FUNCTION FOR Q5**
        :return (List[int]): index of selected action for each agent
        """
        actions = []
        for i in range(self.num_agents):
            uniform = np.random.uniform(low=0.0, high=1.0, size=1)

            if uniform <= self.epsilon:
                actions.append(np.random.choice(range(self.n_acts[i])))
                
            else:
                act_vals = [self.q_tables[i][action] for action in range(self.n_acts[i])]
                actions.append(np.argmax(act_vals))

        return actions

    def learn(
        self, actions: List[int], rewards: List[float], dones: List[bool]
    ) -> List[float]:
        """Updates the Q-tables based on agents' experience
        **YOU MUST IMPLEMENT THIS FUNCTION FOR Q5**
        :param action (List[int]): index of applied action of each agent
        :param rewards (List[float]): received reward for each agent
        :param dones (List[bool]): flag indicating whether a terminal state has been reached for each agent
        :return (List[float]): updated Q-values for current actions of each agent
        """
        updated_values = []
        ### PUT YOUR CODE HERE ###
        for i in range(self.num_agents):
            action = actions[i]
            reward = rewards[i]
            done = dones[i]

            q_old = self.q_tables[i][action]

            q_next = max([self.q_tables[i][act] for act in range(self.n_acts[i])]) if not done else 0
            self.q_tables[i][action] = q_old +  self.learning_rate * (reward + self.gamma * q_next - q_old )
            updated_values.append(self.q_tables[i][action])

        return updated_values

    def schedule_hyperparameters(self, timestep: int, max_timestep: int):
        """Updates the hyperparameters
        **YOU MUST IMPLEMENT THIS FUNCTION FOR Q5**
        This function is called before every episode and allows you to schedule your
        hyperparameters.
        :param timestep (int): current timestep at the beginning of the episode
        :param max_timestep (int): maximum timesteps that the training loop will run for
        """
        ### PUT YOUR CODE HERE ###
        self.epsilon = 1.0 - (min(1.0, timestep/(0.08 * max_timestep))) * 0.95


class JointActionLearning(MultiAgent):
    """
    Agents using the Joint Action Learning algorithm with Opponent Modelling
    **YOU NEED TO IMPLEMENT FUNCTIONS IN THIS CLASS**
    """

    def __init__(self, learning_rate: float =0.5, epsilon: float =1.0, **kwargs):
        """Constructor of JointActionLearning
        :param learning_rate (float): learning rate for Q-learning updates
        :param epsilon (float): epsilon value for all agents
        :attr q_tables (List[DefaultDict]): tables for Q-values mapping joint actions ACTs
            to respective Q-values for all agents
        :attr models (List[DefaultDict]): each agent holding model of other agent
            mapping other agent actions to their counts
        Initializes some variables of the Joint Action Learning agents, namely the epsilon, discount rate and learning rate
        """

        super().__init__(**kwargs)
        self.learning_rate = learning_rate
        self.epsilon = epsilon
        self.n_acts = [flatdim(action_space) for action_space in self.action_spaces]

        # initialise Q-tables for all agents
        self.q_tables: List[DefaultDict] = [defaultdict(lambda: 0) for _ in range(self.num_agents)]

        # initialise models for each agent mapping state to other agent actions to count of other agent action
        # in state
        self.models = [defaultdict(lambda: 0) for _ in range(self.num_agents)] 

    def act(self) -> List[int]:
        """Implement the epsilon-greedy action selection here for stateless task
        **YOU MUST IMPLEMENT THIS FUNCTION FOR Q5**
        :return (List[int]): index of selected action for each agent
        """
        joint_action = []
        ### PUT YOUR CODE HERE ###
        for i in range(self.num_agents):

            uniform = np.random.uniform(low=0.0, high=1.0, size=1)
        
            if uniform < self.epsilon: 
                joint_action.append(np.random.choice(range(self.n_acts[i])))

            else:
                j = (i+1) % 2
                evs = []
                for actions in range(self.n_acts[i]):
                    ev = 0
                    for actions_opponent in range(self.n_acts[j]):
                        ev += (self.models[i][actions_opponent]/max(1, sum(self.models[i].values()))) * self.q_tables[i][(actions,actions_opponent)]
                    evs.append(ev)
                max_acts = [i for i,ev in enumerate(evs) if ev == max(evs)] # argmax EV(a_i)
                joint_action.append(np.random.choice(max_acts))

        return joint_action

    def learn(
        self, actions: List[int], rewards: List[float], dones: List[bool]
    ) -> List[float]:
        """Updates the Q-tables and models based on agents' experience
        **YOU MUST IMPLEMENT THIS FUNCTION FOR Q5**
        :param action (List[int]): index of applied action of each agent
        :param rewards (List[float]): received reward for each agent
        :param dones (List[bool]): flag indicating whether a terminal state has been reached for each agent
        :return (List[float]): updated Q-values for current observation-action pair of each agent
        """
        updated_values = []

        for i in range(self.num_agents):
            reward = rewards[i]
            done = dones[i]

            joint_actions_other_agents = actions[:i] + actions[i+1:]
            self.models[i][joint_actions_other_agents[0]] += 1      #C_a(-i) = C_a(-i) + 1
            q_old = self.q_tables[i][tuple(actions)]

            j = (i + 1) % 2
            evs = []

            for action_next in range(self.n_acts[i]):
                ev_action_next = 0
                for action_next_opponent in range(self.n_acts[j]):
                    ev_action_next += (self.models[i][action_next_opponent]/max(1, sum(self.models[i].values())))*self.q_tables[i][(action_next,action_next_opponent)]
                evs.append(ev_action_next)

            ev = max(evs) if not done else 0
            self.q_tables[i][tuple(actions)] = q_old + self.learning_rate * (reward + self.gamma * ev - q_old)  # Q_a <- Q_a + alpha*[r_i + gamma*EV - Q_a]
            updated_values.append(self.q_tables[i][tuple(actions)])

        return updated_values

    def schedule_hyperparameters(self, timestep: int, max_timestep: int):
        """Updates the hyperparameters
        **YOU MUST IMPLEMENT THIS FUNCTION FOR Q5**
        This function is called before every episode and allows you to schedule your
        hyperparameters.
        :param timestep (int): current timestep at the beginning of the episode
        :param max_timestep (int): maximum timesteps that the training loop will run for
        """
        ### PUT YOUR CODE HERE ###
        self.epsilon = 1.0 - (min(1.0, timestep / (0.08 * max_timestep))) * 0.95