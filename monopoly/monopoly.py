"""
Monopoly stochastic analysis package for Python

Copyright 2026 Jason M. Sachs

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import numpy as np
from enum import Enum
from dataclasses import dataclass

class Space(Enum):
    """
    Symbolic constants for Monopoly spaces
    
    The trailing . is shorthand for Avenue
    (translated in __new__)
    """
    GO              = (0,  'Go')
    MEDITERRANEAN   = (1,  'Mediterranean.')
    COMM_CHEST_S    = (2,  'Community Chest (S)')
    BALTIC          = (3,  'Baltic.')
    INCOME_TAX      = (4,  'Income Tax')
    READING_RR      = (5,  'Reading Railroad')
    ORIENTAL        = (6,  'Oriental.')
    CHANCE_S        = (7,  'Chance (S)')
    VERMONT         = (8,  'Vermont.')
    CONNECTICUT     = (9,  'Connecticut.')
    JUST_VISITING   = (10, 'Just Visiting')
    ST_CHARLES      = (11, 'St. Charles Place')
    ELECTRIC_CO     = (12, 'Electric Company')
    STATES          = (13, 'States.')
    VIRGINIA        = (14, 'Virginia.')
    PENNSYLVANIA_RR = (15, 'Pennsylvania Railroad')
    ST_JAMES        = (16, 'St. James Place')
    COMM_CHEST_W    = (17, 'Community Chest (W)')
    TENNESSEE       = (18, 'Tennessee.')
    NEW_YORK        = (19, 'New York.')
    FREE_PARKING    = (20, 'Free Parking')
    KENTUCKY        = (21, 'Kentucky.')
    CHANCE_N        = (22, 'Chance (N)')
    INDIANA         = (23, 'Indiana.')
    ILLINOIS        = (24, 'Illinois.')
    B_O_RR          = (25, 'B. & O. Railroad')
    ATLANTIC        = (26, 'Atlantic.')
    VENTNOR         = (27, 'Ventnor.')
    WATER_WORKS     = (28, 'Water Works')
    MARVIN_GARDENS  = (29, 'Marvin Gardens')
    JAIL            = (30, 'Jail')
    PACIFIC         = (31, 'Pacific.')
    NORTH_CAROLINA  = (32, 'North Carolina.')
    COMM_CHEST_E    = (33, 'Community Chest (E)')
    PENNSYLVANIA    = (34, 'Pennsylvania.')
    SHORT_LINE_RR   = (35, 'Short Line')
    CHANCE_E        = (36, 'Chance (E)')
    PARK_PLACE      = (37, 'Park Place')
    LUXURY_TAX      = (38, 'Luxury Tax')
    BOARDWALK       = (39, 'Boardwalk')

    # https://docs.python.org/3/howto/enum.html#when-to-use-new-vs-init
    # https://stackoverflow.com/a/12680149/44330
    def __new__(cls, index, description):
        obj = object.__new__(cls)
        obj._value_ = index
        if description.endswith('.'):
            description = description[:-1] + ' Avenue'
        obj.description = description
        return obj
    
    def advance_by(self, n: int) -> Space:
        start = Space.JUST_VISITING if self is Space.JAIL else self
        return Space((start.value + n) % len(Space))    
    def __lt__(self, other: Space) -> bool:
        return self.value < other.value
    def __gt__(self, other: Space) -> bool:
        return self.value > other.value
    def __le__(self, other: Space) -> bool:
        return self.value <= other.value
    def __ge__(self, other: Space) -> bool:
        return self.value >= other.value
    
    def board_index(self, ndoubles:int) -> int:
        return ndoubles*40 + self.value
    def is_chance(self) -> bool:
        return self.name.startswith('CHANCE_')
    def is_community_chest(self) -> bool:
        return self.name.startswith('COMM_CHEST_')

class Card(Enum):
    COMMCHEST_LIFE_INSURANCE_MATURES      = 0
    COMMCHEST_PAY_HOSPITAL                = 1
    COMMCHEST_RECEIVE_FOR_SERVICES        = 2
    COMMCHEST_XMAS_FUND_MATURES           = 3
    COMMCHEST_SALE_OF_STOCK               = 4
    COMMCHEST_GO_TO_JAIL                  = 5
    COMMCHEST_DOCTORS_FEE                 = 6
    COMMCHEST_GET_OUT_OF_JAIL_FREE        = 7
    COMMCHEST_INHERIT                     = 8
    COMMCHEST_COLLECT_FROM_EVERY_PLAYER   = 9
    COMMCHEST_BANK_ERROR                  = 10
    COMMCHEST_ADVANCE_TO_GO               = 11
    COMMCHEST_PAY_SCHOOL_TAX              = 12
    COMMCHEST_INCOME_TAX_REFUND           = 13
    COMMCHEST_SECOND_PRIZE_BEAUTY_CONTEST = 14
    COMMCHEST_STREET_REPAIRS              = 15

    CHANCE_ADVANCE_TO_ILLINOIS_AVE        = 16
    CHANCE_PAY_POOR_TAX                   = 17
    CHANCE_ADVANCE_TO_NEAREST_RAILROAD_1  = 18
    CHANCE_ADVANCE_TO_NEAREST_RAILROAD_2  = 19
    CHANCE_GET_OUT_OF_JAIL_FREE           = 20
    CHANCE_GO_BACK_THREE_SPACES           = 21
    CHANCE_ELECTED_CHAIRMAN_OF_BOARD      = 22
    CHANCE_ADVANCE_TO_NEAREST_UTILITY     = 23
    CHANCE_ADVANCE_TO_GO                  = 24
    CHANCE_ADVANCE_TO_ST_CHARLES_PLACE    = 25
    CHANCE_GENERAL_REPAIRS                = 26
    CHANCE_ADVANCE_TO_BOARDWALK           = 27
    CHANCE_BANK_PAYS_DIVIDEND             = 28
    CHANCE_BUILDING_LOAN_MATURES          = 29
    CHANCE_RIDE_ON_READING_RAILROAD       = 30
    CHANCE_GO_TO_JAIL                     = 31
    
class DrawCardProbability:
    def __init__(self):
        self.chance_cards = self.init_chance_cards()
        self.commchest_cards = self.init_commchest_cards()
        self.space_jumps = {
            Card.COMMCHEST_ADVANCE_TO_GO:              Space.GO,
            Card.COMMCHEST_GO_TO_JAIL:                 Space.JAIL,

            Card.CHANCE_ADVANCE_TO_BOARDWALK:          Space.BOARDWALK,
            Card.CHANCE_ADVANCE_TO_ST_CHARLES_PLACE:   Space.ST_CHARLES,
            Card.CHANCE_ADVANCE_TO_ILLINOIS_AVE:       Space.ILLINOIS,
            Card.CHANCE_ADVANCE_TO_GO:                 Space.GO,
            Card.CHANCE_ADVANCE_TO_NEAREST_RAILROAD_1: lambda space: self.advance_nearest_railroad(space),
            Card.CHANCE_ADVANCE_TO_NEAREST_RAILROAD_2: lambda space: self.advance_nearest_railroad(space),
            Card.CHANCE_ADVANCE_TO_NEAREST_UTILITY:    lambda space: self.advance_nearest_utility(space),
            Card.CHANCE_GO_BACK_THREE_SPACES:          lambda space: space.advance_by(-3),
            Card.CHANCE_GO_TO_JAIL:                    Space.JAIL,
            Card.CHANCE_RIDE_ON_READING_RAILROAD:      Space.READING_RR
        }
    def init_chance_cards(self):
        return [card for card in Card
                if card.name.startswith('CHANCE_') and self.include_card(card)]
    def init_commchest_cards(self):
        return [card for card in Card
                if card.name.startswith('COMMCHEST_') and self.include_card(card)]
    def include_card(self, card):
        return True
    def draw_card(self, space: Space):
        if space.is_chance():
            yield from self.card_outcomes(space, self.chance_cards)
        elif space.is_community_chest():
            yield from self.card_outcomes(space, self.commchest_cards)
        else:
            yield (space, 1)
    def card_outcomes(self, space:Space, cards):
        ncards = len(cards)
        no_move_cards = set(card
                            for card in cards 
                            if self.space_jumps.get(card) is None)
        if no_move_cards:
            yield (space, len(no_move_cards)/ncards) 
        for card in cards:
            nextspace = self.space_jumps.get(card)
            if nextspace is None:
                continue
            if callable(nextspace):
                nextspace = nextspace(space)
            yield (nextspace, 1/ncards)
    def advance_nearest_utility(self, space:Space):
        if space < Space.ELECTRIC_CO or space >= Space.WATER_WORKS:
            return Space.ELECTRIC_CO
        else:
            return Space.WATER_WORKS
    def advance_nearest_railroad(self, space:Space):
        if space < Space.READING_RR or space >= Space.SHORT_LINE_RR:
            return Space.READING_RR
        elif space < Space.PENNSYLVANIA_RR:
            return Space.PENNSYLVANIA_RR
        elif space < Space.B_O_RR:
            return Space.B_O_RR
        else:
            return Space.SHORT_LINE_RR

class MarkovChain:
    def __init__(self):
        self.init()
        
    def init(self):
        ...
        # Required property: transitions matrix

    def calculate_frequency_info(self):
        """
        Returns a tuple (freq, eigv2), where
         
          freq = frequency vector of steady-state values,
          eigv2 = magnitude of the 2nd-largest eigenvalue
        """
        T = self.transitions
        # Find eigenvectors
        eigval, V = np.linalg.eig(T)
        ii = np.abs(eigval - 1.0) < 1e-12
        
        # Find the index of eigenvalue 1, and test assertions
        # 1. There should be only one such eigenvalue
        assert sum(ii) == 1
        # 2. All other eigenvalues are smaller
        assert (np.abs(eigval[~ii]) < 1).all()
        i = np.nonzero(ii)[0][0]
        Vp = V[:,i]
        # 3. All eigenvector values are real
        assert (Vp.imag == 0).all()
        Vp = Vp.real
        freq = Vp / sum(Vp)
        eigv2 = np.sort(np.abs(eigval))[-2]
        return freq, eigv2

@dataclass
class MonopolyTransition:
    space:     Space
    ndoubles:  int
    pipchance: float

    def describe(self):
        return '%3d: #%d %-21s p=%r/36' % (self.state,
                                           self.ndoubles, 
                                           self.space.description, 
                                           self.pipchance)
    @property
    def state(self):
        return self.space.board_index(self.ndoubles)

    @property
    def probability(self):
        return self.pipchance/36

class MonopolyChain(MarkovChain):
    def init(self):
        self.dcp = self.initDrawCardProbability()
        self.transitions = np.zeros((120,120))
        for space in Space:
            for ndoubles in range(3):
                colindex = space.board_index(ndoubles)
                for transition in self.transitions_from(space, ndoubles):
                    rowindex = transition.space.board_index(transition.ndoubles)
                    self.transitions[rowindex, colindex] += transition.probability
                ptotal = self.transitions[:,colindex].sum()
                assert np.abs(ptotal-1) < 1e-10

    def initDrawCardProbability(self):
        return DrawCardProbability()

    def transitions_from(self, space:Space, ndoubles:int):
        """
        Yield MonopolyTransition for each possible next space
        """

        # Jail on first two turns is special: you stay there if not rolling doubles
        if space is Space.JAIL and ndoubles < 2:
            yield MonopolyTransition(space, ndoubles+1, 30)   # stay in jail if we didn't role doubles
            # doubles
            for sum_dice in range(2,13,2):
                nextspace = space.advance_by(sum_dice)
                yield from self.transitions_after_landing_on(nextspace, pipchance=1, ndoubles=0)
                # no further rolls after leaving JAIL        
        
        else:   # not JAIL, or third turn after entering JAIL
            for sum_dice in range(2,13):
                nextspace = space.advance_by(sum_dice)
                # probability of this sum
                pipchance= min(sum_dice - 1, 13 - sum_dice)
                if sum_dice % 2 == 0 and space is not Space.JAIL: # even roll, but not getting out of jail
                    # doubles
                    if ndoubles == 2:
                        yield MonopolyTransition(Space.JAIL, 0, 1)
                    else:
                        yield from self.transitions_after_landing_on(nextspace, pipchance=1, ndoubles=ndoubles+1)
                    pipchance -= 1
                # not doubles:
                if pipchance > 0:
                    yield from self.transitions_after_landing_on(nextspace, pipchance=pipchance, ndoubles=0)

    def transitions_after_landing_on(self, space:Space, pipchance:int, ndoubles:int):
        for nextspace, p in self.dcp.draw_card(space):
            # special case: Chance -> Community Chest
            if space != nextspace and nextspace.is_community_chest():
                yield from self.transitions_after_landing_on(nextspace, pipchance*p, ndoubles)
            # normal case: 
            else:
                yield MonopolyTransition(nextspace, 
                                        (0 if nextspace is Space.JAIL else ndoubles),
                                        pipchance*p)
                
    def get_space_transition_table(self, space: int | Space, concise_format=False):
        """
        describe all transitions from space in pipchances (1/36 probability)
        """
        import pandas as pd

        if isinstance(space, int):
            space = Space(space)
        i0 = space.value
        T = self.transitions[:, [i0, i0+40, i0+80]] * 36
        df = pd.DataFrame(np.hstack(T.reshape(3, 40, 3)))
        df.columns = pd.MultiIndex.from_tuples(
                        [(i, j) for i in range(3) for j in range(3)],
                        names=['to_doubles','from_doubles']
                    )
        df = df.swaplevel(axis=1).sort_index(axis=1)
        df.insert(0, ('','#'), np.arange(40))
        df.index = [space.description for space in Space]
        df.name = 'Probability (pipchances) from %s' % space.description
        if concise_format:
            # show only nonzero rows and nonzero spaces
            def format_val(x):
                if x == 0:
                    return ''
                elif x == int(x):
                    return '%d' % x
                else:
                    return '%g' % x
            ii = (df.iloc[:,1:10] != 0).any(axis=1)
            result = df.loc[ii,:].style
            # add a CSS class so we can align the row headings to the left
            result.set_table_attributes('class="align-row-heading-left"')
            return result.format(format_val, subset=df.columns[1:])
        else:
            return df

            
    def get_frequency_table(self):
        import pandas as pd
        
        freq, eigv2 = self.calculate_frequency_info()
        freq = freq.reshape(3,40)
        p_jail = freq[:, Space.JAIL.value].sum()
        turn_per_roll = freq[0,:].sum() + p_jail - freq[0, Space.JAIL.value]
        # total probability of states that end a turn
        # (don't count (0, JAIL) twice!)
        
        p_end_of_turn = freq[0,:] / turn_per_roll
        p_end_of_turn[Space.JAIL.value] = p_jail / turn_per_roll
        df = pd.DataFrame({'space':[space.description for space in Space], 
                           0:freq[0,:], 1:freq[1,:], 2:freq[2,:],
                           'end of roll':freq.sum(axis=0),
                           'end of turn':p_end_of_turn,
                           'during turn':freq.sum(axis=0) / turn_per_roll})
        df['rank'] = df['during turn'].rank(ascending=False).astype(int)
        return df
        