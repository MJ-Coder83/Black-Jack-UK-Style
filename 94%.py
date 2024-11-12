import random
import collections
import sys
import time
import itertools

# Ranks and suits for a standard deck of cards
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']

DEBUG_FLAGS = {
    "all": False,
    "player": False,
    "ai": False,
    "cards": False,
    "game": False
}

special_cards = {}

class AIPlayer:
    def __init__(self, name, difficulty):
        self.name = name
        self.difficulty = difficulty
        self.card_count = collections.defaultdict(int)
        self.performance_score = 0        
        self.strategy_weights = {'play_high': 0.5, 'play_low': 0.5, 'play_run': 0.5}
        self.last_action = None
        self.player_model = collections.defaultdict(lambda: collections.defaultdict(int))

    def __str__(self):
        return f"{self.name}[{self.difficulty.capitalize()}]"

    def play_turn(self, hand, top_card, valid_single_cards, valid_runs):
        if DEBUG_FLAGS["all"] or DEBUG_FLAGS["ai"]:
            print(f"DEBUG [AI]: {self} is deciding on a move")
        if self.difficulty == 'easy':
            return self.play_easy(valid_single_cards, valid_runs)
        elif self.difficulty == 'medium':
            return self.play_medium(hand, valid_single_cards, valid_runs)
        elif self.difficulty == 'hard':
            return self.play_hard(hand, valid_single_cards, valid_runs)
        elif self.difficulty == 'adaptive':
            if self.performance_score > 0:
                return self.play_hard(hand, valid_single_cards, valid_runs)
            elif self.performance_score < 0:
                return self.play_easy(valid_single_cards, valid_runs)
            else:
                return self.play_medium(hand, valid_single_cards, valid_runs)
        else:  # learning
            return self.play_learning(hand, valid_single_cards, valid_runs)

    def play_easy(self, valid_single_cards, valid_runs):
        if valid_runs:
            choice = random.randint(1, len(valid_runs))
            if DEBUG_FLAGS["all"] or DEBUG_FLAGS["ai"]:
                print(f"DEBUG [AI]: {self} chose to play run {choice}")
            return 2, choice
        elif valid_single_cards:
            choice = random.randint(1, len(valid_single_cards))
            if DEBUG_FLAGS["all"] or DEBUG_FLAGS["ai"]:
                print(f"DEBUG [AI]: {self} chose to play single card {choice}")
            return 1, choice
        else:
            if DEBUG_FLAGS["all"] or DEBUG_FLAGS["ai"]:
                print(f"DEBUG [AI]: {self} chose to draw a card")
            return 3, None

    def play_medium(self, hand, valid_single_cards, valid_runs):
        if valid_runs:
            longest_run = max(valid_runs, key=lambda x: len(x.split(' - ')))
            choice = valid_runs.index(longest_run) + 1
            if DEBUG_FLAGS["all"] or DEBUG_FLAGS["ai"]:
                print(f"DEBUG [AI]: {self} chose to play run {choice}")
            return 2, choice
        elif valid_single_cards:
            highest_card = max(valid_single_cards, key=lambda x: ranks.index(x.split()[0]))
            choice = valid_single_cards.index(highest_card) + 1
            if DEBUG_FLAGS["all"] or DEBUG_FLAGS["ai"]:
                print(f"DEBUG [AI]: {self} chose to play single card {choice}")
            return 1, choice
        else:
            if DEBUG_FLAGS["all"] or DEBUG_FLAGS["ai"]:
                print(f"DEBUG [AI]: {self} chose to draw a card")
            return 3, None

    def play_hard(self, hand, valid_single_cards, valid_runs):
        if random.random() < 0.1:  # 10% chance to bluff
            return self.bluff(valid_single_cards, valid_runs)

        count_score = self.get_card_count_score()
        predicted_action = self.predict_player_action('human_player', len(hand))

        if len(hand) == 1 and valid_single_cards:
            if DEBUG_FLAGS["all"] or DEBUG_FLAGS["ai"]:
                print(f"DEBUG [AI]: {self} chose to play last card")
            return 1, 1  # Play the last card if possible
        elif count_score > 5 and valid_single_cards:  # More low cards have been played
            highest_card = max(valid_single_cards, key=lambda x: ranks.index(x.split()[0]))
            choice = valid_single_cards.index(highest_card) + 1
            if DEBUG_FLAGS["all"] or DEBUG_FLAGS["ai"]:
                print(f"DEBUG [AI]: {self} chose to play highest card {choice}")
            return 1, choice
        elif count_score < -5:  # More high cards have been played
            if valid_single_cards:
                lowest_card = min(valid_single_cards, key=lambda x: ranks.index(x.split()[0]))
                choice = valid_single_cards.index(lowest_card) + 1
                if DEBUG_FLAGS["all"] or DEBUG_FLAGS["ai"]:
                    print(f"DEBUG [AI]: {self} chose to play lowest card {choice}")
                return 1, choice
            else:
                if DEBUG_FLAGS["all"] or DEBUG_FLAGS["ai"]:
                    print(f"DEBUG [AI]: {self} chose to draw a card")
                return 3, None  # Draw a card
        elif predicted_action == 'play_run' and valid_single_cards:
            return self.play_highest_card(valid_single_cards)
        elif valid_runs:
            best_run = max(valid_runs, key=lambda x: len(x.split(' - ')))
            choice = valid_runs.index(best_run) + 1
            if DEBUG_FLAGS["all"] or DEBUG_FLAGS["ai"]:
                print(f"DEBUG [AI]: {self} chose to play run {choice}")
            return 2, choice
        elif valid_single_cards:
            non_ace_cards = [card for card in valid_single_cards if 'Ace' not in card]
            if non_ace_cards:
                highest_card = max(non_ace_cards, key=lambda x: ranks.index(x.split()[0]))
            else:
                highest_card = valid_single_cards[0]
            choice = valid_single_cards.index(highest_card) + 1
            if DEBUG_FLAGS["all"] or DEBUG_FLAGS["ai"]:
                print(f"DEBUG [AI]: {self} chose to play single card {choice}")
            return 1, choice
        else:
            if DEBUG_FLAGS["all"] or DEBUG_FLAGS["ai"]:
                print(f"DEBUG [AI]: {self} chose to draw a card")
            return 3, None

    def play_learning(self, hand, valid_single_cards, valid_runs):
        if valid_runs and random.random() < self.strategy_weights['play_run']:
            self.last_action = 'play_run'
            return self.play_best_run(valid_runs)
        elif valid_single_cards:
            if random.random() < self.strategy_weights['play_high']:
                self.last_action = 'play_high'
                return self.play_highest_card(valid_single_cards)
            else:
                self.last_action = 'play_low'
                return self.play_lowest_card(valid_single_cards)
        else:
            if DEBUG_FLAGS["all"] or DEBUG_FLAGS["ai"]:
                print(f"DEBUG [AI]: {self} chose to draw a card")
            return 3, None

    def update_card_count(self, card):
        rank = card.split(' of ')[0]
        self.card_count[rank] += 1

    def get_card_count_score(self):
        score = 0
        for rank, count in self.card_count.items():
            if rank in ['10', 'Jack', 'Queen', 'King', 'Ace']:
                score -= count
            elif rank in ['2', '3', '4', '5', '6']:
                score += count
        return score

    def update_player_model(self, player, action, hand_size):
        self.player_model[player][action] += 1
        self.player_model[player]['hand_size'] = hand_size
    
    def choose_suit(self, hand):
        if self.difficulty == 'easy':
            return random.choice(suits)
        elif self.difficulty == 'medium':
            suit_counts = collections.Counter(card.split(' of ')[1] for card in hand)
            return max(suit_counts, key=suit_counts.get)
        elif self.difficulty in ['hard', 'adaptive']:
            suit_counts = collections.Counter(card.split(' of ')[1] for card in hand)
            max_count = max(suit_counts.values())
            best_suits = [suit for suit, count in suit_counts.items() if count == max_count]
            return random.choice(best_suits) if best_suits else random.choice(suits)
        else:  # learning
            suit_weights = {suit: self.strategy_weights.get(f'choose_{suit.lower()}', 0.25) for suit in suits}
            return random.choices(list(suit_weights.keys()), weights=suit_weights.values())[0]

    def bluff(self, valid_single_cards, valid_runs):
        if valid_single_cards:
            choice = random.randint(1, len(valid_single_cards))
            if DEBUG_FLAGS["all"] or DEBUG_FLAGS["ai"]:
                print(f"DEBUG [AI]: {self} is bluffing with single card {choice}")
            return 1, choice
        elif valid_runs:
            choice = random.randint(1, len(valid_runs))
            if DEBUG_FLAGS["all"] or DEBUG_FLAGS["ai"]:
                print(f"DEBUG [AI]: {self} is bluffing with run {choice}")
            return 2, choice
        else:
            if DEBUG_FLAGS["all"] or DEBUG_FLAGS["ai"]:
                print(f"DEBUG [AI]: {self} failed to bluff, drawing a card")
            return 3, None
        
    def learn(self, reward):
        if self.last_action:
            self.strategy_weights[self.last_action] += reward

    def adjust_difficulty(self, result):
        if result == 'win':
            self.performance_score += 1
        else:
            self.performance_score -= 1

        if self.performance_score > 3:
            self.difficulty = 'hard'
        elif self.performance_score < -3:
            self.difficulty = 'easy'
        else:
            self.difficulty = 'medium'

    def predict_player_action(self, player, context):
        if context in self.player_model[player]:
            return max(self.player_model[player][context], key=self.player_model[player][context].get)
        return None

    def play_best_run(self, valid_runs):
        best_run = max(valid_runs, key=lambda x: len(x.split(' - ')))
        choice = valid_runs.index(best_run) + 1
        if DEBUG_FLAGS["all"] or DEBUG_FLAGS["ai"]:
            print(f"DEBUG [AI]: {self.name} chose to play best run {choice}")
        return 2, choice

    def play_highest_card(self, valid_single_cards):
        highest_card = max(valid_single_cards, key=lambda x: ranks.index(x.split()[0]))
        choice = valid_single_cards.index(highest_card) + 1
        if DEBUG_FLAGS["all"] or DEBUG_FLAGS["ai"]:
            print(f"DEBUG [AI]: {self.name} chose to play highest card {choice}")
        return 1, choice

    def play_lowest_card(self, valid_single_cards):
        lowest_card = min(valid_single_cards, key=lambda x: ranks.index(x.split()[0]))
        choice = valid_single_cards.index(lowest_card) + 1
        if DEBUG_FLAGS["all"] or DEBUG_FLAGS["ai"]:
            print(f"DEBUG [AI]: {self.name} chose to play lowest card {choice}")
        return 1, choice
    
class GameState:
    def __init__(self, players):
        self.players = players
        self.ai_players = {player.name: player for player in players if isinstance(player, AIPlayer)}
        self.current_player_index = 0
        self.direction = 1  # 1 for clockwise, -1 for counter-clockwise
        self.pick_up_stack = 0
        self.potential_winner = None
        self.last_effect = None
        self.current_suit = None
        self.player_hands = {}
        self.missed_turns = {player: 0 for player in players}  # New: track missed turns for each player

    def next_player(self):
        while True:
            self.current_player_index = (self.current_player_index + self.direction) % len(self.players)
            current_player = self.players[self.current_player_index]
            if self.missed_turns[current_player] > 0:
                self.missed_turns[current_player] -= 1
                print_boxed(f"{current_player} misses this turn.")
                print('-' * 73)
                confirm_to_proceed()
            else:
                return current_player

    def reverse_direction(self):
        self.direction *= -1
        direction_name = "clockwise" if self.direction == 1 else "counter-clockwise"
        print(f"Direction changed to {direction_name}")
        print('-' * 73)
        self.display_turn_order()

    def display_turn_order(self):
        current_index = self.current_player_index
        order = []
        for i in range(len(self.players)):
            player = self.players[(current_index + i * self.direction) % len(self.players)]
            player_name = player.name if isinstance(player, AIPlayer) else str(player)
            if i == 0:
                order.append(f"{player_name} *")
            elif i == 1:
                order.append(f"{player_name} ^")
            else:
                order.append(player_name)
        direction_name = "clockwise" if self.direction == 1 else "counter-clockwise"
        print(f"TURN ORDER ({direction_name}): {' -> '.join(order)}")
        print('-' * 73)

    def set_potential_winner(self, player):
        self.potential_winner = player

    def get_potential_winner(self):
        return self.potential_winner

    def has_potential_winner(self):
        return self.potential_winner is not None

    def clear_potential_winner(self):
        self.potential_winner = None

    def declare_winner(self, player):
        print_boxed(f"{player} wins the game!")
        return "game_over"

def confirm_to_proceed():
    input("Press Enter to continue...")
    print('-' * 73)
    
def is_pickup_card(card):
    rank = card.split(' of ')[0]
    return any(term in get_special_effect_name(card) for term in ['Pick Up Two', 'Pick Up Five'])

def find_pickup_runs(hand):
    pickup_cards = [card for card in hand if is_pickup_card(card)]
    
    if not pickup_cards:
        return []

    # Generate all possible combinations of pick-up cards
    runs = []
    for i in range(2, len(pickup_cards) + 1):  # Start from 2 to only consider actual runs
        runs.extend(itertools.combinations(pickup_cards, i))
    
    # Sort runs by length (descending) and then alphabetically
    runs.sort(key=lambda x: (-len(x), x))
    
    return runs

def is_cover_card(card):
    return get_special_effect_name(card) == "Cover"

def has_pickup_card(hand):
    return any(is_pickup_card(card) for card in hand)

def draw_new_card(player, hand, deck):
    if deck:
        new_card = deck.pop(0)
        hand.append(new_card)
        
        if isinstance(player, AIPlayer):
            print_boxed(f"{player} drew 1 card.")
        else:
            print_boxed(f"{player} drew: {new_card}")
    else:
        print_boxed("The deck is empty. Cannot draw a new card.")
        
def slow_print(text, delay=0.5):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
        print()  # Print a newline at the end of the text

    # Example usage:
    #slow_print("This text will be printed slowly.")
        
def configure_debugging():
    global DEBUG_FLAGS
    current_state = "On" if any(DEBUG_FLAGS.values()) else "Off"
    
    while True:
        print(f"\nConfigure debugging (current state: {current_state})")
        choice = input("Do you want to change debugging settings? (y/n): ").lower()
        
        if choice != 'y':
            break
        
        print("1. All debugging on")
        print("2. All debugging off")
        print("3. Player debugging on")
        print("4. Player debugging off")
        print("5. Cards debugging on")
        print("6. Cards debugging off")
        print("7. Game debugging on")
        print("8. Game debugging off")
        
        debug_choice = input("Enter your choice: ")
        
        if debug_choice == '1':
            DEBUG_FLAGS = {key: True for key in DEBUG_FLAGS}
        elif debug_choice == '2':
            DEBUG_FLAGS = {key: False for key in DEBUG_FLAGS}
        elif debug_choice == '3':
            DEBUG_FLAGS["player"] = True
        elif debug_choice == '4':
            DEBUG_FLAGS["player"] = False
        elif debug_choice == '5':
            DEBUG_FLAGS["cards"] = True
        elif debug_choice == '6':
            DEBUG_FLAGS["cards"] = False
        elif debug_choice == '7':
            DEBUG_FLAGS["game"] = True
        elif debug_choice == '8':
            DEBUG_FLAGS["game"] = False
        else:
            print("Invalid choice. Please try again.")
        
        current_state = "On" if any(DEBUG_FLAGS.values()) else "Off"
    
    print("Debug configuration complete.")
    print('-' * 73)

def configure_special_cards():
    global special_cards
    setup_default_special_cards()  # Start with default assignments
    
    effects = {
        1: "Pick Up Two",
        2: "Pick Up Five",
        3: "Miss a Turn",
        4: "Cover",
        5: "Cancel",
        6: "Reverse",
        7: "Change Suit"
    }
    
    while True:
        print("\nCurrent Special Card Assignments:")
        for card, effect in special_cards.items():
            print(f"{card}: {effects[effect]}")
        
        choice = input("\nEnter the name of the card you want to reassign (or 'done' to finish): ")
        if choice.lower() == 'done':
            break
        
        if choice in special_cards or choice.split()[0] in special_cards:
            print(f"\nReassigning {choice}")
            print("Available effects:")
            for num, effect in effects.items():
                print(f"{num}. {effect}")
            
            while True:
                effect_choice = input("Enter the number of the new effect: ")
                if effect_choice.isdigit() and 1 <= int(effect_choice) <= 7:
                    if ' of ' in choice:  # Full card name
                        special_cards[choice] = int(effect_choice)
                    else:  # Just the rank
                        special_cards[choice.split()[0]] = int(effect_choice)
                    print(f"{choice} has been assigned the effect: {effects[int(effect_choice)]}")
                    break
                else:
                    print("Invalid choice. Please enter a number between 1 and 7.")
        else:
            print("Invalid card name. Please try again.")

def get_special_effect_name(card):
    parts = card.split(' of ')
    if len(parts) >= 2:
        rank = parts[0]
    else:
        rank = card

    if card in special_cards:
        effect = special_cards[card]
    elif rank in special_cards:
        effect = special_cards[rank]
    else:
        return ""

    effect_names = {
        1: "Pick Up Two",
        2: "Pick Up Five",
        3: "Miss a Turn",
        4: "Cover",
        5: "Cancel",
        6: "Reverse",
        7: "Change Suit"
    }
    return effect_names.get(effect, "")

def create_deck():
    """Create a standard deck of 52 cards."""
    deck = [f'{rank} of {suit}' for rank in ranks for suit in suits]
    return deck

def shuffle_deck(deck):
    """Shuffle the deck of cards."""
    random.shuffle(deck)
    return deck

def deal_cards(deck, players, cards_per_player):
    """Deal cards to each player."""
    player_hands = {player: deck[i*cards_per_player:(i+1)*cards_per_player] for i, player in enumerate(players)}
    remaining_deck = deck[len(players)*cards_per_player:]
    return player_hands, remaining_deck

def sort_cards(cards):
    def card_sort_key(card):
        rank, suit = card.split(' of ')
        return (ranks.index(rank), suits.index(suit))
    return sorted(cards, key=card_sort_key)

def find_valid_single_cards(hand, top_card):
    """Find valid single cards that can be played."""
    top_rank, top_suit = top_card.split(' of ')
    valid_single_cards = [
        card for card in hand if 
        'Ace' in card or  # Aces can be played on any card
        top_suit in card or  # Same suit
        card.split(' of ')[0] == top_rank  # Same rank
         
    ]
    return valid_single_cards

def find_valid_runs(hand, top_card, valid_single_cards):
    """Find valid runs including consecutive, rank match, and combination runs."""

    valid_runs = []
    max_run_length = len(hand)  # Limit the maximum run length to the number of cards in hand
    
    def get_rank(card):
        return card.split(' of ')[0]

    def get_suit(card):
        return card.split(' of ')[1]

    def get_next_rank(rank):
        rank_index = ranks.index(rank)
        return ranks[(rank_index + 1) % len(ranks)]

    def get_prev_rank(rank):
        rank_index = ranks.index(rank)
        return ranks[(rank_index - 1) % len(ranks)]

    def extend_run(start_card, direction):
        run = [start_card]
        current_rank = get_rank(start_card)
        current_suit = get_suit(start_card)
        
        while len(run) < max_run_length:
            if direction == 'forward':
                next_rank = get_next_rank(current_rank)
            else:
                next_rank = get_prev_rank(current_rank)
            
            next_card = f"{next_rank} of {current_suit}"
            
            if next_card in hand:
                run.append(next_card)
                current_rank = next_rank
            else:
                break
        
        return run

    def find_rank_matches(card):
        rank = get_rank(card)
        return [c for c in hand if get_rank(c) == rank and c != card]

    def build_combination_run(current_run):
        if len(current_run) > 1:
            valid_runs.append(' - '.join(current_run))
            valid_runs.append(' - '.join(reversed(current_run)))  # Add the reversed combination run
        
        if len(current_run) >= max_run_length:
            return  # Stop recursion if the run length reaches the maximum

        last_card = current_run[-1]
        rank_matches = find_rank_matches(last_card)
        
        for match in rank_matches:
            if match not in current_run:  # Avoid duplicates in the run
                new_run = current_run + [match]
                build_combination_run(new_run)
        
        next_card = f"{get_next_rank(get_rank(last_card))} of {get_suit(last_card)}"
        prev_card = f"{get_prev_rank(get_rank(last_card))} of {get_suit(last_card)}"
        
        if next_card in hand and next_card not in current_run:  # Avoid duplicates
            new_run = current_run + [next_card]
            build_combination_run(new_run)
        
        if prev_card in hand and prev_card not in current_run:  # Avoid duplicates
            new_run = current_run + [prev_card]
            build_combination_run(new_run)

    for start_card in valid_single_cards:
        # Consecutive runs (forward and backward)
        for direction in ['forward', 'backward']:
            run = extend_run(start_card, direction)
            for i in range(2, len(run) + 1):
                valid_runs.append(' - '.join(run[:i] if direction == 'forward' else run[-i:]))

        # Rank match runs
        rank_matches = [card for card in hand if get_rank(card) == get_rank(start_card) and card != start_card]
        if rank_matches:
            valid_runs.append(f"{start_card} - {' - '.join(rank_matches)}")

        # Combination runs
        build_combination_run([start_card])

    # Filter out runs that don't start with a valid single card
    valid_runs = [run for run in valid_runs if run.split(' - ')[0] in valid_single_cards]

    # Remove duplicates and sort
    valid_runs = sorted(list(set(valid_runs)))

    return valid_runs

def add_special_indicator(card):
    effect_name = get_special_effect_name(card)
    if effect_name:
        return f"{card}[{effect_name}]"
    return card

    if is_ai:
        print(f"{player}'s hand: {len(hand)} cards")
        print('-' * 73)
    else:
        sorted_hand = sort_cards(hand)
        hand_with_indicators = [add_special_indicator(card) for card in sorted_hand]
        message = (f"CURRENT HAND:\n" + "{', '.join(hand_with_indicators)}")
        print_dashed_box = message
        #print('-' * 73)

def print_centered(text, width=73, fill_char=' '):
    print(f"{text.center(width, fill_char)}")

def print_wrapped(text, width=73, indent=0, is_card_run=False):
    def wrap_card_run(cards, max_width):
        lines = []
        current_line = []
        current_length = 0
        for card in cards:
            if current_length == 0 or current_length + len(card) + 4 <= max_width:  # +4 for " -> " separator
                current_line.append(card)
                current_length += len(card) + (4 if current_length > 0 else 0)
            else:
                lines.append(current_line)
                current_line = [card]
                current_length = len(card)
        if current_line:
            lines.append(current_line)
        return lines

    if is_card_run:
        cards = text.split(' - ')
        wrapped_lines = wrap_card_run(cards, width - indent)
        for line in wrapped_lines:
            print(' ' * indent + ' -> '.join(line))
    else:
        # Split the input text into lines
        lines = text.split('\n')
        
        for line in lines:
            # Preserve leading spaces
            leading_spaces = len(line) - len(line.lstrip())
            line = line.strip()
            
            # If the line is empty, print a blank line
            if not line:
                print()
                continue
            
            # Initialize the current line
            current_line = ' ' * (indent + leading_spaces)
            
            # Split the line into words
            words = line.split()
            
            for word in words:
                # If adding the word doesn't exceed the width, add it to the current line
                if len(current_line) + len(word) + 1 <= width:
                    if current_line.strip():
                        current_line += ' '
                    current_line += word
                else:
                    # Print the current line and start a new one
                    print(current_line)
                    current_line = ' ' * (indent + leading_spaces) + word
            
            # Print any remaining text
            if current_line.strip():
                print(current_line)

def print_boxed(text, width=73, alignments=None):
    def wrap_text(text, max_width):
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        for word in words:
            if current_length + len(word) + len(current_line) <= max_width:
                current_line.append(word)
                current_length += len(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
        if current_line:
            lines.append(' '.join(current_line))
            return lines

    def wrap_card_run(cards, max_width):
        lines = []
        current_line = []
        current_length = 0
        for card in cards:
            if current_length == 0 or current_length + len(card) + 4 <= max_width:  # +4 for " -> " separator
                current_line.append(card)
                current_length += len(card) + (4 if current_length > 0 else 0)
            else:
                lines.append(current_line)
                current_line = [card]
                current_length = len(card)
        if current_line:
            lines.append(current_line)
            return lines

    def align_text(line, align, max_width):
        if align == 'left':
            return line.ljust(max_width)
        elif align == 'right':
            return line.rjust(max_width)
        else:  # center
            return line.center(max_width)

    print('┌' + '─' * (width - 2) + '┐')
    
    # Split the text into lines
    text_lines = text.split('\n')
    
    # If alignments are not specified, default to center alignment for all lines
    if alignments is None:
        alignments = ['center'] * len(text_lines)
    # If alignments is a string, apply it to all lines
    elif isinstance(alignments, str):
        alignments = [alignments] * len(text_lines)
    # Ensure we have an alignment for each line
    alignments = alignments + ['left'] * (len(text_lines) - len(alignments))

    # Process each line
    for line_index, (line, align) in enumerate(zip(text_lines, alignments)):
        if line_index == 1 and ' - ' in line:  # Assume second line is card run if it contains ' - '
            cards = line.split(' - ')
            wrapped_cards = wrap_card_run(cards, width - 6)  # -6 for "│  " and "  │" on each side
            for card_line in wrapped_cards:
                card_text = " -> ".join(card_line)
                centered_text = card_text.center(width-6)
                print(f"│  {centered_text}  │")
        else:
            wrapped_lines = wrap_text(line, width - 4)
            for wrapped_line in wrapped_lines:
                aligned_line = align_text(wrapped_line, align, width - 4)
                print(f"│ {aligned_line} │")

    print('└' + '─' * (width - 2) + '┘')

def print_dashed_box(text, width=73, title_alignment='center'):
    def wrap_cards(cards, max_width):
        lines = []
        current_line = []
        current_length = 0
        for card in cards:
            if current_length == 0 or current_length + len(card) + 3 <= max_width:  # +3 for " | " separator
                current_line.append(card)
                current_length += len(card) + (3 if current_length > 0 else 0)
            else:
                lines.append(current_line)
                current_line = [card]
                current_length = len(card)
        if current_line:
            lines.append(current_line)
        return lines

    print('-' * width)
    
    # Split the text into lines
    text_lines = text.split('\n')
    
    # Handle the title (first line)
    title = text_lines[0]
    if title_alignment == 'left':
        print(f"| {title.ljust(width-4)} |")
    elif title_alignment == 'right':
        print(f"| {title.rjust(width-4)} |")
    else:  # center
        print(f"|{title.center(width-2)}|")
    
    # Handle additional lines if present
    if len(text_lines) > 1:
        for line in text_lines[1:]:
            cards = line.split(', ')
            wrapped_cards = wrap_cards(cards, width - 4)  # -4 for "| |" on each side
            
            for card_line in wrapped_cards:
                card_text = " | ".join(card_line)
                print(f"| {card_text.ljust(width-4)} |")
    
    print('-' * width)

def display_game_stats(deck, discard_pile, top_card, player_hands):
    print_boxed("Round Statistics")
    print(f"Number of cards in the deck: {len(deck)}")
    print(f"Number of cards in the discard pile: {len(discard_pile)}")
    print(f"Top card: {top_card}")
    print("Player hands:")
    for player, hand in player_hands.items():
        print(f"{player}: {len(hand)} cards")
    print('-' * 73)
    confirm_to_proceed()

# Example usage in the game loop:
# display_game_stats(deck, discard_pile, top_card, player_hands)

def display_game_start(game_number):
    start_text = (f"Starting Game {game_number}")
    print_boxed(start_text)
    print(' >< ' * 18)

def display_turn_header(current_player, turn_count):
    #print('-' * 60)
    print_boxed(f"{current_player}'s Turn (Turn {turn_count})")
    print('-' * 73)

def display_top_card(top_card):
    print_centered(f"──── TOP CARD: {add_special_indicator(top_card)} ────")
    #print('-' * 73)

def display_player_hand(player, hand, is_ai=False, title_alignment='left'):
    if is_ai:
        print('-' * 73)
        print(f"{player}'s HAND: {len(hand)} cards")
        print('-' * 73)
    else:
        sorted_hand = sort_cards(hand)
        hand_with_indicators = [add_special_indicator(card) for card in sorted_hand]
        hand_text = f"{player}'s HAND:\n" + ", ".join(hand_with_indicators)
        print_dashed_box(hand_text, width=73, title_alignment=title_alignment)
        #print('-' * 60)

def setup_default_special_cards():
    global special_cards
    special_cards = {
        "2": 1,  # Pick Up Two
        "Jack of Clubs": 2,  # Pick Up Five
        "Jack of Spades": 2,  # Pick Up Five
        "8": 3,  # Miss a Turn
        "Queen": 4,  # Cover
        "Jack of Hearts": 5,  # Cancel
        "Jack of Diamonds": 5,  # Cancel
        "King": 6,  # Reverse
        "Ace": 7  # Change Suit
    }

def debug_print_deck_size(deck, discard_pile):
    if DEBUG_FLAGS["all"] or DEBUG_FLAGS["game"]:
        print(f"DEBUG [GAME]: Cards in deck: {len(deck)}, Cards in discard pile: {len(discard_pile)}")

def apply_special_effect(played_cards, current_player, game_state, hand=None):
    if isinstance(played_cards, str):
        return apply_single_card_effect(played_cards, current_player, game_state, hand)
    else:
        new_top_card = played_cards[-1]  # The last card in the run becomes the new top card
        last_rank = new_top_card.split(' of ')[0]
        special_effects = []
        
        # Find the last rank-matched cards
        for card in reversed(played_cards):
            if card.split(' of ')[0] == last_rank:
                if card in special_cards or last_rank in special_cards:
                    special_effects.insert(0, card)  # Insert at the beginning to maintain order
            else:
                break  # Stop when we hit a different rank

        # Apply effects
        for card in special_effects:
            apply_single_card_effect(card, current_player, game_state)
        
        # Display total pick up stack after processing all cards in the run
        if game_state.pick_up_stack > 0:
            #print(f"Total Pick up stack after run: {game_state.pick_up_stack}")
        
            return get_special_effect_name(new_top_card), new_top_card

def apply_single_card_effect(played_card, current_player, game_state, hand=None):
    parts = played_card.split(' of ')
    if len(parts) >= 2:
        rank = parts[0]
    else:
        rank = played_card
        
    if played_card in special_cards:
        effect = special_cards[played_card]
    elif rank in special_cards:
        effect = special_cards[rank]
    else:
        if DEBUG_FLAGS["all"] or DEBUG_FLAGS["cards"]:
            print(f"DEBUG [CARDS]: No special effect for {played_card}")
            print('-' * 73)
        return None, played_card  # No special effect for this card

    effect_names = {
        1: "Pick Up Two",
        2: "Pick Up Five",
        3: "Miss a Turn",
        4: "Cover",
        5: "Cancel",
        6: "Reverse",
        7: "Change Suit"
    }

    effect_name = effect_names.get(effect, str(effect))

    if DEBUG_FLAGS["all"] or DEBUG_FLAGS["cards"]:
        print(f"DEBUG [CARDS]: Applying effect {effect_name} for {played_card}")
        print('-' * 73)
        
    if effect == 1:  # Pick up two
        game_state.pick_up_stack += 2
        game_state.last_effect = "pick up"
        print_boxed(f"The Pick Up Stack is now {game_state.pick_up_stack}")
        print('-' * 73)
        if DEBUG_FLAGS["all"] or DEBUG_FLAGS["cards"]:
            print(f"DEBUG [CARDS]: Pick Up Stack increased to {game_state.pick_up_stack}")
            print('-' * 73)
        return "pick up", played_card

    elif effect == 2:  # Pick up five
        game_state.pick_up_stack += 5
        game_state.last_effect = "pick up"
        print_boxed(f"The Pick Up Stack is now {game_state.pick_up_stack}")
        print('-' * 73)
        if DEBUG_FLAGS["all"] or DEBUG_FLAGS["cards"]:
            print(f"DEBUG [CARDS]: Pick Up Stack increased to {game_state.pick_up_stack}")
            print('-' * 73)
        return "pick up", played_card

    elif effect == 3:  # Miss a Turn
        num_miss_cards = 1  # Default to 1 for a single card
        apply_miss_turn_effect(game_state, current_player, num_miss_cards)
        if DEBUG_FLAGS["all"] or DEBUG_FLAGS["cards"]:
            print(f"DEBUG [CARDS]: Miss a Turn effect applied for {num_miss_cards} card(s)")
            print('-' * 73)
        return "skip", played_card

    elif effect == 4:  # Cover
        cover_card_name = add_special_indicator(played_card)
        game_state.last_effect = "cover"
        game_state.cover_card = cover_card_name
        #print('-' * 73)
        #confirm_to_proceed()
        if DEBUG_FLAGS["all"] or DEBUG_FLAGS["cards"]:
            print(f"DEBUG [CARDS]: {current_player} must cover {cover_card_name} or draw a card")
            print('-' * 73)
        return "cover", played_card
    
    elif effect == 5:  # Cancel
        if game_state.last_effect == "pick up":
            print_centered(f"The Pick Up is canceled. Pick Up stack is now 0.")
            print('-' * 73)
            game_state.pick_up_stack = 0
        game_state.last_effect = None
        if DEBUG_FLAGS["all"] or DEBUG_FLAGS["cards"]:
            print(f"DEBUG [CARDS]: Cancel effect applied, Pick Up stack reset to 0")
        return "cancel", played_card
    
    elif effect == 6:  # Reverse
        game_state.reverse_direction()
        new_direction = "clockwise" if game_state.direction == 1 else "counter-clockwise"
        if DEBUG_FLAGS["all"] or DEBUG_FLAGS["cards"]:
            print(f"DEBUG [CARDS]: Direction reversed to {new_direction}")
        return "reverse", played_card

    elif effect == 7:  # Change Suit
        if DEBUG_FLAGS["all"] or DEBUG_FLAGS["cards"]:
            print(f"DEBUG [CARDS]: Current player: {current_player}")
            print(f"DEBUG [CARDS]: Is AIPlayer? {isinstance(current_player, AIPlayer)}")
            print('-' * 73)

        if isinstance(current_player, AIPlayer):
            if DEBUG_FLAGS["all"] or DEBUG_FLAGS["cards"]:
                print(f"DEBUG [CARDS]: Entering AI branch for change suit")
                print(f"DEBUG [CARDS]: AI difficulty: {current_player.difficulty}")
            try:
                new_suit = current_player.choose_suit(game_state.player_hands[current_player])
                if DEBUG_FLAGS["all"] or DEBUG_FLAGS["cards"]:
                    print(f"DEBUG [CARDS]: AI chose suit: {new_suit}")
            except Exception as e:
                if DEBUG_FLAGS["all"] or DEBUG_FLAGS["cards"]:
                    print(f"DEBUG [CARDS]: Error in AI choose_suit: {str(e)}")
                new_suit = choose_suit_human()  # Choose a random suit as a fallback
        else:
            if DEBUG_FLAGS["all"] or DEBUG_FLAGS["cards"]:
                print("DEBUG [CARDS]: Entering human branch for change suit")
            new_suit = choose_suit_human(hand)

        print_boxed(f"{current_player} changes the suit to {new_suit}!")
        print('-' * 73)
        new_top_card = f"{played_card.split(' of ')[0]} of {new_suit}"        
        #confirm_to_proceed()  # Ensure this is called only once
        #print('-' * 73)
        if DEBUG_FLAGS["all"] or DEBUG_FLAGS["cards"]:
            print(f"DEBUG [CARDS]: New TOP CARD: {new_top_card}")
            print(f"DEBUG [CARDS]: Suit changed to {new_suit}")
            print('-' * 73)
        return "change suit", new_top_card

    return None, played_card  # Default return if no special effect is applied

def choose_suit_human(hand=None):
    if hand:
        sorted_hand = sort_cards(hand)
        hand_with_indicators = [add_special_indicator(card) for card in sorted_hand]
        boxhand = (f"CURRENT HAND:\n{', '.join(hand_with_indicators)}")
        print_dashed_box(boxhand, width=73, title_alignment='left')
    print("Change Suit:")
    for i, suit in enumerate(suits, 1):
        print(f"{i}. {suit}")
    while True:
        choice = input("Choose suit: ")
        print('-' * 73)
        if choice.isdigit() and 1 <= int(choice) <= len(suits):
            return suits[int(choice) - 1]
        print("Invalid choice. Please enter a number from the menu.")
        print('-' * 73)

def apply_special_effect(played_cards, current_player, game_state, hand=None):
    if isinstance(played_cards, str):
        return apply_single_card_effect(played_cards, current_player, game_state, hand)
    else:
        return apply_run_effect(played_cards, current_player, game_state)

def apply_run_effect(played_cards, current_player, game_state):
    new_top_card = played_cards[-1]
    last_rank = new_top_card.split(' of ')[0]
    special_effects = []
    miss_turn_count = 0
    final_effect = None
    change_suit_card = None
    
    for card in reversed(played_cards):
        if card.split(' of ')[0] == last_rank:
            if card in special_cards or last_rank in special_cards:
                special_effects.insert(0, card)
        else:
            break

    if special_effects:
        for card in special_effects:
            effect = special_cards.get(card, special_cards.get(last_rank))
            effect_name = get_special_effect_name(card)
            
            if effect_name == 'Miss a Turn':
                miss_turn_count += 1
            elif effect_name == 'Change Suit':
                change_suit_card = card  # Store the last Change Suit card
            elif effect_name in ['Cover', 'Cancel']:
                # Apply these effects once
                effect, _ = apply_single_card_effect(card, current_player, game_state)
                final_effect = effect
            else:
                # For other stacking effects, apply based on the number of special cards
                effect, _ = apply_single_card_effect(card, current_player, game_state)
                final_effect = effect

        if miss_turn_count > 0:
            apply_miss_turn_effect(game_state, current_player, miss_turn_count)
            final_effect = "skip"

        if change_suit_card:
            # Apply only the last Change Suit effect
            effect, new_top_card = apply_single_card_effect(change_suit_card, current_player, game_state)
            final_effect = effect

    return final_effect, new_top_card

def ai_turn_delay(seconds=3):
    #print(f"Player turn complete.............")
    #print('-' * 60)
    time.sleep(seconds)
    #print("Continuing to next turn.")

def apply_miss_turn_effect(game_state, current_player, num_miss_cards=1):
    num_players = len(game_state.players)
    current_player_index = game_state.players.index(current_player)

    for i in range(num_miss_cards):
        # Calculate the index of the next player who should miss a turn
        next_player_index = (current_player_index + (i + 1) * game_state.direction) % num_players
        next_player = game_state.players[next_player_index]

        # Apply the miss turn effect to the next player
        game_state.missed_turns[next_player] += 1
        #print_boxed(f"{next_player} will miss {game_state.missed_turns[next_player]} turn(s).")
        #print('-' * 73)
    
def play_turn(player_hands, deck, top_card, current_player, discard_pile, game_state, stats, ai_player=None):
    if DEBUG_FLAGS["all"] or DEBUG_FLAGS["player"] or DEBUG_FLAGS["ai"]:
        print(f"DEBUG [PLAYER/AI]: Entering play_turn function for {current_player}")
        print('-' * 73)
    try:    
        player_name = current_player if isinstance(current_player, str) else current_player.name
        hand = player_hands[current_player]

        is_ai_player = isinstance(current_player, AIPlayer)
        ai_player = current_player if is_ai_player else None
        
        display_top_card(top_card)
        display_player_hand(current_player, hand, is_ai=ai_player is not None, title_alignment='left')

        valid_single_cards = find_valid_single_cards(hand, top_card)
        valid_runs = find_valid_runs(hand, top_card, valid_single_cards)

        if DEBUG_FLAGS["all"] or DEBUG_FLAGS["ai"]:
            print('-' * 73)
            print_wrapped(f"DEBUG [PLAYER/AI]: Valid single cards for {current_player}: {valid_single_cards}\n")
            print_wrapped(f"DEBUG [PLAYER/AI]: Valid runs for {current_player}: {valid_runs}")
            print('-' * 73)

        if game_state.pick_up_stack > 0:
            pickup_runs = find_pickup_runs(hand)
            single_pickup_cards = [card for card in hand if is_pickup_card(card)]
            cancel_cards = [card for card in hand if get_special_effect_name(card) == "Cancel"]

            if pickup_runs or single_pickup_cards or cancel_cards:
                if ai_player:
                    if pickup_runs:
                        action = '2'
                    elif single_pickup_cards:
                        action = '3'
                    elif cancel_cards:
                        action = '3'
                    else:
                        action = '1'
                else:
                    while True:
                        print(f"You must respond to the Pick Up effect. Current stack: {game_state.pick_up_stack}")
                        print("1. Draw cards (Pick Up Stack)")
                        if pickup_runs:
                            print("2. Play a run of Pick Up cards")
                        if single_pickup_cards or cancel_cards:
                            print("3. Play a single Pick Up or Cancel card")
                        action = input("Enter your choice: ")
                        print('-' * 73)
                        if action in ['1', '2', '3'] and (action != '2' or pickup_runs) and (action != '3' or (single_pickup_cards or cancel_cards)):
                            break
                        print("Invalid input. Please enter a valid option.")
                        print('-' * 73)
            else:
                action = '1'

            if action == '1':
                drawn_cards = []
                for _ in range(game_state.pick_up_stack):
                    if deck:
                        card_drawn = deck.pop(0)
                        hand.append(card_drawn)
                        drawn_cards.append(card_drawn)
                    else:
                        print("The deck is empty. Cannot pick up more cards.")
                        break
                
                if drawn_cards:
                    if isinstance(current_player, AIPlayer):
                        print_boxed(f"{current_player} drew {len(drawn_cards)} cards.")
                    else:
                        card_list = ", ".join(drawn_cards)
                        print_boxed(f"{current_player} drew {len(drawn_cards)} cards:\n{card_list}")
                else:
                    print_boxed(f"{current_player} couldn't draw any cards.")
                
                print('-' * 73)
                game_state.pick_up_stack = 0
                return top_card, "draw", False

            elif action == '2':  # Play a run of Pick Up cards
                if ai_player:
                    chosen_run = pickup_runs[0]  # AI chooses longest run
                else:
                    while True:
                        print("Choose a run to play:")
                        for i, run in enumerate(pickup_runs, 1):
                            run_str = " -> ".join([add_special_indicator(card) for card in run])
                            print(f"{i}. {run_str}")
                        run_choice = input("Enter your choice: ")
                        print('-' * 73)
                        if run_choice.isdigit() and 1 <= int(run_choice) <= len(pickup_runs):
                            chosen_run = pickup_runs[int(run_choice) - 1]
                            break
                        print("Invalid choice. Please enter a number from the list.")
                        print('-' * 73)

                for card in chosen_run:
                    hand.remove(card)
                    effect, new_top_card = apply_special_effect(card, current_player, game_state, hand)

                run_str = " -> ".join([add_special_indicator(card) for card in chosen_run])
                print_boxed(f"{current_player} played a run:\n{run_str}")
                print("-------------------------------------------------------------------------")

                if len(hand) == 0:
                    game_state.set_potential_winner(current_player)
                    print(f"{current_player} played their last card(s). The next player must respond or {current_player} wins.")

                return new_top_card, "run", False

            elif action == '3':  # Play a single Pick Up or Cancel card
                playable_cards = single_pickup_cards + cancel_cards
                if ai_player:
                    chosen_card = playable_cards[0]
                else:
                    while True:
                        print("Choose a card to play:")
                        for i, card in enumerate(playable_cards, 1):
                            print(f"{i}. {add_special_indicator(card)}")
                        card_choice = input("Enter your choice: ")
                        print('-' * 73)
                        if card_choice.isdigit() and 1 <= int(card_choice) <= len(playable_cards):
                            chosen_card = playable_cards[int(card_choice) - 1]
                            break
                        print("Invalid choice. Please enter a number from the list.")
                        print('-' * 73)

                hand.remove(chosen_card)
                print_boxed(f"{current_player} played:\n{add_special_indicator(chosen_card)}")
                print("-------------------------------------------------------------------------")
                effect, new_top_card = apply_special_effect(chosen_card, current_player, game_state, hand)

                if effect == "cancel":
                    game_state.pick_up_stack = 0
                elif len(hand) == 0:
                    game_state.set_potential_winner(current_player)
                    print(f"{current_player} played their last card. The next player must respond or {current_player} wins.")

                return new_top_card, "single", False

        while True:  # Main loop for action selection
            if ai_player:
                action, choice = ai_player.play_turn(hand, top_card, valid_single_cards, valid_runs)
                if DEBUG_FLAGS["all"] or DEBUG_FLAGS["ai"]:
                    print(f"DEBUG [AI]: {current_player} chose action {action} with choice {choice}")
            else:
                if not valid_single_cards and not valid_runs:
                    if not deck:
                        print_boxed("The deck is empty. Skipping turn.")
                        return top_card, "skip", False
                    
                    card_drawn = deck.pop(0)
                    hand.append(card_drawn)
                    print_boxed("No valid cards or runs to play. You have drawn 1 card.")
                    print("-------------------------------------------------------------------------")
                    print_boxed(f"Card drawn: {card_drawn}")
                    print('-' * 73)
                    return top_card, "draw", False

                print("AVAILABLE ACTIONS:")
                if valid_single_cards:
                    print("1. Play a single card")
                if valid_runs:
                    print("2. Play a run")
                print("3. Draw from the deck")
                print('-' * 73)
                action = input("Enter the number of your choice: ")
                print('-' * 73)
                if action not in ['1', '2', '3']:
                    print("Invalid action. Please choose a valid option.")
                    print('-' * 73)
                    continue

            if action == '1' or (ai_player and action == 1):
                if not valid_single_cards:
                    print_boxed(f"No valid single cards to play. {current_player} will draw a card.")
                    continue
                
                if ai_player:
                    card_index = choice - 1
                else:
                    while True:
                        print("VALID SINGLE CARDS:")
                        for idx, card in enumerate(valid_single_cards, start=1):
                            print(f"{idx}. {add_special_indicator(card)}")
                        print('-' * 73)
                        choice = input("Choose a card to play (or 0 to go back): ")
                        print('-' * 73)
                        if choice == '0':
                            break
                        try:
                            card_index = int(choice) - 1
                            if 0 <= card_index < len(valid_single_cards):
                                break
                            else:
                                print(f"Invalid card number. Please try again.")
                                print('-' * 73)
                        except ValueError:
                            print("Invalid input. Please enter a number.")
                    
                    if choice == '0':
                        continue  # Go back to main action selection

                played_card = valid_single_cards[card_index]
                if played_card not in hand:
                    print(f"Error: {played_card} not in {current_player}'s hand!")
                    return top_card, "error", False
                hand.remove(played_card)
                print_boxed(f"{current_player} played:\n {add_special_indicator(played_card)}")
                print("-------------------------------------------------------------------------")
                if ai_player:
                    ai_player.update_card_count(played_card)
                    
                effect, new_top_card = apply_special_effect(played_card, current_player, game_state, hand)
                
                if len(hand) == 0:
                    if get_special_effect_name(played_card) == "Miss a Turn":
                        if count_active_opponents(game_state) > 1:
                            print_boxed(f"{current_player} has won the game!")
                            confirm_to_proceed()
                            return new_top_card, "win", False
                        else:
                            draw_new_card(current_player, hand, deck)
                            print_boxed(f"{current_player} played a 'Miss a Turn' card as their last card, but must draw a new card as only one opponent remains.")
                            confirm_to_proceed()
                            return new_top_card, "continue", False
                    elif is_pickup_card(played_card):
                        game_state.set_potential_winner(current_player)
                        print_boxed(f"{current_player} played their last card (Pick Up). The next player must respond or {current_player} wins.")
                        confirm_to_proceed()
                        return new_top_card, "pick up last", False
                    elif is_cover_card(played_card):
                        print_boxed(f"{current_player} played their last card (Cover), but must draw a new card.")
                        confirm_to_proceed()
                        draw_new_card(current_player, hand, deck)
                        return new_top_card, "single", False
                    else:
                        print_boxed(f"{current_player} has won the game!")
                        confirm_to_proceed()
                        return new_top_card, "win", False
                        
                return new_top_card, "single", effect == "cover"

            elif action == '2' or (ai_player and action == 2):
                if not valid_runs:
                    print(f"No valid runs to play.")
                    print('-' * 73)
                    continue
                
                if ai_player:
                    run_index = choice - 1
                else:
                    while True:
                        print("VALID RUNS:")
                        for idx, run in enumerate(valid_runs, start=1):
                            cards_in_run = run.split(' - ')
                            cards_with_indicators = [add_special_indicator(card) for card in cards_in_run]
                            print(f"{idx}. {' -> '.join(cards_with_indicators)}")
                        print('-' * 73)
                        choice = input("Choose a run to play (or 0 to go back): ")
                        print('-' * 73)
                        if choice == '0':
                            break
                        try:
                            run_index = int(choice) - 1
                            if 0 <= run_index < len(valid_runs):
                                break
                            else:
                                print(f"Invalid run number. Please try again.")
                        except ValueError:
                            print("Invalid input. Please enter a number.")
                    
                    if choice == '0':
                        continue  # Go back to main action selection

                played_run = valid_runs[run_index].split(' - ')

                # Update longest run statistic
                run_length = len(played_run)
                stats[current_player]["longest_run"] = max(stats[current_player]["longest_run"], run_length)

                missing_cards = [card for card in played_run if card not in hand]
                if missing_cards:
                    print(f"Error: The following cards are not in your hand: {', '.join(missing_cards)}")
                    print("Please try again.")
                    print('-' * 73)
                    continue
                
                for card in played_run:
                    hand.remove(card)
                    
                played_run_with_indicators = ' - '.join([add_special_indicator(card) for card in played_run])
                print_boxed(f"{current_player} played:\n {played_run_with_indicators}")
                print("-------------------------------------------------------------------------")
                if ai_player:
                    for card in played_run:
                        ai_player.update_card_count(card)
                
                # Add all cards in the run (except the last card) to the discard pile
                discard_pile.extend(played_run[:-1])
                
                last_card = played_run[-1]
                effect, new_top_card = apply_special_effect(played_run, current_player, game_state)
                
                if len(hand) == 0:
                    print_boxed(f"{current_player} has won the game!")
                    confirm_to_proceed()
                    return new_top_card, "win", False
                
                return new_top_card, "run", effect == "cover"

            elif action == '3' or (ai_player and action == 3):
                if DEBUG_FLAGS["all"] or DEBUG_FLAGS["ai"]:
                    print(f"DEBUG [AI]: {current_player} is drawing a card")
                    print('-' * 73)
                
                if not deck:
                    print_boxed("The deck is empty. Reshuffling discarded cards.")
                    if not discard_pile:
                        print("No cards to reshuffle. Skipping draw.")
                        return top_card, "skip", False
                    deck.extend(discard_pile)
                    discard_pile.clear()
                    shuffle_deck(deck)

                if deck:
                    card_drawn = deck.pop(0)
                    hand.append(card_drawn)
                    message = f"{current_player} drew 1 card from deck."
                    if not ai_player:
                        message += f" - {card_drawn}"
                else:
                    message = f"{current_player} attempted to draw, but the deck is empty."
            
                print_boxed(message)
                print('-' * 73)
                    
                return top_card, "draw", False

        # This part should never be reached, but just in case:
        print("Unexpected end of turn reached.")
        return top_card, "error", False

    except Exception as e:
        print(f"An error occurred in play_turn: {str(e)}")
        import traceback
        traceback.print_exc()
        return top_card, "error", False
    
def count_active_opponents(game_state):
    current_player = game_state.players[game_state.current_player_index]
    return sum(1 for p in game_state.players if p != current_player and len(game_state.player_hands[p]) > 0)
    
def play_game(num_real_players, num_bot_players, num_decks, cards_per_player, ai_difficulties):
    deck = create_deck() * num_decks
    deck = shuffle_deck(deck)
    num_players = num_real_players + num_bot_players
    
    players = [f'PLAYER {i+1}' for i in range(num_real_players)]
    ai_players = {}
    for i in range(num_bot_players):
        ai_player_name = f'AI PLAYER {i+1}'
        difficulty = ai_difficulties[ai_player_name]
        ai_player = AIPlayer(ai_player_name, difficulty)
        ai_players[ai_player_name] = ai_player
        players.append(ai_player)  # Append the AIPlayer object, not a string
    
    player_hands, deck = deal_cards(deck, players, cards_per_player)
    top_card = deck.pop(0)
    discard_pile = []
    
    game_state = GameState(players)
    game_state.player_hands = player_hands
    
    turn_count = 1
    round_count = 1
    stats = {player: {"cards_drawn": 0, "runs_played": 0, "single_cards_played": 0, "longest_run": 0} for player in players}
    
    while True:
        for _ in range(num_players):
            # Check if the deck needs reshuffling
            if len(deck) <= 18:
                print_boxed("Reshuffling the deck with the discard pile.")
                confirm_to_proceed()
                deck.extend(discard_pile)
                discard_pile = [top_card]  # Keep the top card out of the new deck
                shuffle_deck(deck)
                if DEBUG_FLAGS["all"] or DEBUG_FLAGS["game"]:
                    print(f"DEBUG [GAME]: Reshuffled. New deck size: {len(deck)}")
                    print('-' * 73)

            current_player = game_state.players[game_state.current_player_index]
            is_ai_player = isinstance(current_player, AIPlayer)
            ai_player = current_player if is_ai_player else None

            # Check for pending Pick Up win condition
            if game_state.has_potential_winner():
                potential_winner = game_state.get_potential_winner()
                if current_player == potential_winner:
                    print_boxed(f"{potential_winner} wins! No player could respond with a Pick Up card.")
                    return potential_winner, turn_count, stats
                elif not has_pickup_card(player_hands[current_player]):
                    print_boxed(f"{current_player} couldn't respond with a Pick Up card.")
                    print('-' * 73)
                    game_state.next_player()
                    continue
                else:
                    game_state.clear_potential_winner()
            
            display_turn_header(current_player, turn_count)
            game_state.display_turn_order()
            
            if DEBUG_FLAGS["all"] or DEBUG_FLAGS["game"]:
                debug_print_deck_size(deck, discard_pile)
            
            play_again = True
            while play_again:
                if DEBUG_FLAGS["all"] or DEBUG_FLAGS["ai"]:
                    print(f"DEBUG [AI]: Current player: {current_player}, Is AI: {is_ai_player}")
                
                result = play_turn(
                    player_hands, 
                    deck, 
                    top_card, 
                    current_player, 
                    discard_pile, 
                    game_state,
                    stats
                )
                
                if result is None:
                    print(f"DEBUG: play_turn returned None for {current_player}")
                    continue

                new_top_card, action_taken, play_again = result
                
                # Update statistics
                if action_taken == "draw":
                    stats[current_player]["cards_drawn"] += 1
                elif action_taken == "single":
                    stats[current_player]["single_cards_played"] += 1
                elif action_taken == "run":
                    stats[current_player]["runs_played"] += 1

                if action_taken == "win":
                    return current_player, turn_count, stats

                if action_taken == "pick up last":
                    game_state.set_potential_winner(current_player)
                    print(f"{current_player} played their last card (Pick Up). The next player must respond or {current_player} wins.")
                    break  # Exit the play_again loop to move to the next player
                
                if new_top_card is None:
                    print("Game ended due to no more playable cards.")
                    return None, turn_count, stats
                
                if new_top_card != top_card:
                    discard_pile.append(top_card)
                    top_card = new_top_card
                
                # Update AI knowledge (if applicable)
                for ai in ai_players.values():
                    ai.update_player_model(current_player, action_taken, len(player_hands[current_player]))

                if action_taken == "cover":
                    play_again = True
                    print(f"{current_player} gets another turn due to Cover effect!")
                    print('-' * 73)
                    continue
                
                # Check for win condition
                if len(player_hands[current_player]) == 0:
                    # Ensure the last action is recorded in stats if it wasn't already
                    if action_taken == "run" and stats[current_player]["runs_played"] == 0:
                        stats[current_player]["runs_played"] += 1
                    elif action_taken == "single" and stats[current_player]["single_cards_played"] == 0:
                        stats[current_player]["single_cards_played"] += 1
                    
                    #print_boxed(f"{current_player} has won the game!")
                    #print('-' * 73)
                    #confirm_to_proceed()
                    # Adjust AI difficulties and update performance scores
                    for ai in ai_players.values():
                        ai.adjust_difficulty('lose' if ai != current_player else 'win')
                    return current_player, turn_count, stats
            
            if not play_again:
                confirm_to_proceed()  # This will be called after every player's turn
                game_state.next_player()
                turn_count += 1
        
        # Display game statistics at the end of each round
        display_game_stats(deck, discard_pile, top_card, player_hands)

    return None, turn_count, stats

def get_longest_run_players(stats):
    max_run = max(player_stats['longest_run'] for player_stats in stats.values())
    return [player for player, player_stats in stats.items() if player_stats['longest_run'] == max_run]
        
def display_round_summary(winner, turns, stats):
    print_boxed("Game Summary")
    print('-' * 73)
    print(f"Winner: {winner}")
    print(f"Total turns played: {turns}")
    print('-' * 73)
    print("Player Statistics:")
    for player, player_stats in stats.items():
        print('-' * 73)
        print(f"{player}:")
        print(f"Cards drawn: {player_stats['cards_drawn']}")
        print(f"Single cards played: {player_stats['single_cards_played']}")
        print(f"Runs played: {player_stats['runs_played']}")
        print(f"Longest run: {player_stats['longest_run']} cards")
    print('-' * 73)

    longest_run_players = get_longest_run_players(stats)
    max_run_length = stats[longest_run_players[0]]['longest_run']
    
    print('-' * 73)
    if len(longest_run_players) == 1:
        print(f"Longest run of the game: {max_run_length} cards by {longest_run_players[0]}")
    else:
        print(f"Longest run of the game: {max_run_length} cards")
        print(f"Players with the longest run: {', '.join(longest_run_players)}")
    print('-' * 73)

def display_overall_scores(overall_scores):
    print_boxed("Overall Scores (Games Won)")
    print('-' * 73)
    for player, score in overall_scores.items():
        print(f"{player}: {score}")

def display_final_summary(games_played, overall_scores):
    print_boxed("Final Game Summary")
    print('-' * 73)
    print(f"Total games played: {games_played}")
    print("\nFinal Scores (Games Won):")
    for player, score in overall_scores.items():
        print(f"{player}: {score}")
    winner = max(overall_scores, key=overall_scores.get)
    print(f"\nOverall Winner: {winner}")
    print("\nThank you for playing!")
    print('-' * 73)

def get_player_key(player):
    if isinstance(player, AIPlayer):
        return f"{player.name}[{player.difficulty.capitalize()}]"
    return player

def main():
    print_boxed("Welcome to Street Black Jack")
    setup_default_special_cards()  # Set up default special cards
    
    configure_debugging()  # Configure debugging options

    while True:
        try:
            num_decks = int(input("Enter the number of decks (1-4): "))
            if 1 <= num_decks <= 4 :
                break
            else:
                print("Invalid input. Please enter a number between 1 and 4.")
        except ValueError:
            print("Invalid input. Please enter a number between 1 and 4.")
    
    while True:
        try:
            cards_per_player = int(input("Enter the number of cards in hand (1-10): "))
            if 1 <= cards_per_player <= 10:
                break
            else:
                print("Invalid input. Please enter a number between 1 and 10.")
        except ValueError:
            print("Invalid input. Please enter a valid integer.")
    
    configure_special = input("Configure special cards (y/n): ").lower()
    if configure_special == 'y':
        configure_special_cards()
    
    while True:
        try:
            num_real_players = int(input("Enter the number of real players (0-10): "))
            if 0 <= num_real_players <= 10:
                break
            else:
                print("Invalid input. Please enter a number between 0 and 10.")
        except ValueError:
            print("Invalid input. Please enter a valid integer.")
    
    while True:
        try:
            num_bot_players = int(input("Enter the number of AI players (0-10): "))
            if 0 <= num_bot_players <= 10:
                break
            else:
                print("Invalid input. Please enter a number between 0 and 10.")
        except ValueError:
            print("Invalid input. Please enter a valid integer.")
            
    ai_difficulties = {}
    for i in range(num_bot_players):
        print(f"Difficulty level for AI PLAYER {i+1}:")
        print("1. Easy")
        print("2. Medium")
        print("3. Hard")
        print("4. Adaptive")
        print("5. Learning")
        while True:
            difficulty_choice = input("Enter difficulty level: ")
            print('-' * 73)
            if difficulty_choice in ['1', '2', '3', '4', '5']:
                break
            print("Invalid input. Please enter 1, 2, 3, 4, or 5.")
        
        difficulties = ['easy', 'medium', 'hard', 'adaptive', 'learning']
        ai_difficulties[f'AI PLAYER {i+1}'] = difficulties[int(difficulty_choice) - 1]
    
    players = [f'PLAYER {i+1}' for i in range(num_real_players)]
    for i in range(num_bot_players):
        ai_player_name = f'AI PLAYER {i+1}'
        difficulty = ai_difficulties[ai_player_name]
        ai_player = AIPlayer(ai_player_name, difficulty)
        players.append(f'{ai_player_name}[{difficulty.capitalize()}]')

    overall_scores = {get_player_key(player): 0 for player in players}
    games_played = 0
    
    while True:
        games_played += 1
        display_game_start(games_played)
        
        winner, turns, stats = play_game(num_real_players, num_bot_players, num_decks, cards_per_player, ai_difficulties)
        
        winner_key = get_player_key(winner)
        if winner_key in overall_scores:
            overall_scores[winner_key] += 1
        else:
            print(f"Warning: Winner key '{winner_key}' not found in overall_scores.")
            overall_scores[winner_key] = 1  # Initialize score if key doesn't exist
        
        display_round_summary(winner, turns, stats)
        display_overall_scores(overall_scores)
        
        print('-' * 73)
        print("Would you like to play another game?")
        print("1. Yes")
        print("2. No")
        while True:
            choice = input("Enter your choice: ")
            print('-' * 73)
            if choice in ['1', '2']:
                break
            print("Invalid input. Please enter 1 or 2.")
            print('-' * 73)
        
        if choice == '2':
            break
    
    display_final_summary(games_played, overall_scores)

if __name__ == "__main__":
    main()
