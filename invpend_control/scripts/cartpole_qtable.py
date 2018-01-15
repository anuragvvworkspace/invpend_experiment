#!/usr/bin/env python
# Import utilities
import numpy as np
import math
import random
import time
# Import rospy for ros manipulation
import rospy
# Import CartPole class from cartpole.py
from cartpole import CartPole


# Reinforement learning environment related settings
## Discrete actions, states and buckets
ACTIONS = (-1., 0., 1.) # discrete velocity command
NUM_ACTIONS = len(ACTIONS)
upper_bound = [2.4, 1, math.pi/12, math.radians(50)]
lower_bound = [-2.4, -1, -math.pi/12, -math.radians(50)]
STATE_BOUNDS = zip(lower_bound, upper_bound)
NUM_BUCKETS = (3, 3, 6, 3) # (pos_cart, vel_cart, pos_pole, vel_pole)
## Learning related constants
MIN_LEARNING_RATE = 0.1
MIN_EXPLORE_RATE = 0.01
## Simulation related constans
NUM_EPISODES = 1000
MAX_STEP = 250
STREAK_TO_END = 120

class QlearnCartPole(CartPole):
    """ Inherent from CartPole class and add q-learning method """
    def __init__(self):
        CartPole.__init__(self)
        # Q-table
        self.q_table = np.zeros(NUM_BUCKETS + (NUM_ACTIONS,))

    def train(self):
        # Initialize learning
        step = 0
        episode = 0
        learning_rate = get_learning_rate(episode)
        explore_rate = get_explore_rate(episode)
        discount_factor = 0.99
        num_streaks = 0
        # reset environment
        self.reset_env()
        # initial joint states
        ob, _, _ = self.observe_env()
        # map joint states to slot in Q table
        state_0 = observeToBucket(ob)
        # get ready to learn
        rate = rospy.Rate(self.freq)
        while not rospy.is_shutdown():
            # select an action with epsilon greedy, decaying explore_rate
            action_index, action = select_action(state_0, explore_rate)
            # apply action as velocity comand
            self.take_action(action)
            # give the enviroment some time to obtain new observation
            rate.sleep()
            # obtain new observation from environment
            ob, reward, out = self.observe_env()
            # map new observation to slot in Q table
            state = observeToBucket(ob)
            # update Q-table
            max_q = np.amax(self.q_table[state])
            self.q_table[state_0 + (action_index,)] += learning_rate*(reward + discount_factor*max_q - self.q_table[state_0 + (action_index,)])
            if episode <= NUM_EPISODES and num_streaks < STREAK_TO_END:
                if not out and step <= MAX_STEP:
                    state_0 = state
                    step += 1
                else:
                    if step == MAX_STEP:
                        num_streaks += 1
                    else:
                        num_streaks = 0
                    # reset env for next episode
                    self.reset_env()
                    # back to initial joint states
                    ob, _, _ = self.observe_env()
                    # map joint states to slot in Q table
                    state_0 = observeToBucket(ob)
                    episode += 1
                    explore_rate = get_explore_rate(episode)
                    learning_rate = get_learning_rate(episode)
            else:
                # save q_table
                self.clean_shutdown()
            rate.sleep()

# Useful functions
def get_learning_rate(episode):
    return max(MIN_LEARNING_RATE, min(0.5, 1.0-math.log10((episode+1)/25.)))

def get_explore_rate(episode):
    return max(MIN_EXPLORE_RATE, min(1, 1.0-math.log10((episode+1)/25.)))
    
def observeToBucket(state):
    bucket_indice = []
    for i in range(len(state)):
        if state[i] <= STATE_BOUNDS[i][0]:
            bucket_index = 0
        elif state[i] >= STATE_BOUNDS[i][1]:
            bucket_index = NUM_BUCKETS[i] - 1
        else:
            # Mapping the state bounds to the bucket array
            bound_width = STATE_BOUNDS[i][1] - STATE_BOUNDS[i][0]
            offset = (NUM_BUCKETS[i]-1)*STATE_BOUNDS[i][0]/bound_width
            scaling = (NUM_BUCKETS[i]-1)/bound_width
            bucket_index = int(round(scaling*state[i] - offset))
        bucket_indice.append(bucket_index)
    return tuple(bucket_indice)

def select_action(state, explore_rate):
    # Select a random action
    if random.random() < explore_rate:
        act_idx = random.randrange(0,NUM_ACTIONS)
        action = ACTIONS[act_idx]
    # Select the action with the highest q
    else:
        act_idx = np.argmax(self.q_table[state])
        action = ACTIONS[act_idx]
    return act_idx, action

def main():
    """ Set up Q-learning and run """
    print("Initiating simulation...")
    rospy.init_node('q_learning')
    ql_agent = QlearnCartPole()
    rospy.on_shutdown(ql_agent.clean_shutdown)
    ql_agent.train()
    rospy.spin()
    
if __name__ == '__main__':
    main()
