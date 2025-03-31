import csv
from dataclasses import dataclass
import datetime
from enum import StrEnum
from io import StringIO
import logging
import os
from operator import attrgetter
import sys
from typing import List, Optional


COL_NUM = 0
COL_NAME = 1
COL_DATE = 2
COL_TIME = 3
COL_TYPE = 4

class MembershipType(StrEnum):
    ENGAGED = 'E'
    BASIC = 'G'


@dataclass
class Participant:
    """Class for keeping track of all participants"""
    member_number: int
    name: str
    request_date : datetime.datetime
    t: MembershipType

    def __str__(self) -> str:
        return f"{self.name} #{self.member_number} ({self.request_date})"


def main(filename: Optional[str]):
    #Ask User Input!
    if filename:
        if not os.path.isfile(filename):
            logging.error("'%s' is not a valid filename. Try again!", filename)
            return
    else:
        input_data = ask_input()
    available_tickets = ask_available_tickets()
    board_request = ask_board_request()
    winner_lotto = ask_winner_lotto()

    logging.info("========================================================================")

    available_tickets_members = (available_tickets -1) if board_request else available_tickets
    if board_request:
        logging.info("The board requested a Ticket. # Tickets available for members is: %d", available_tickets_members)
    else:
        logging.info("The board has NOT requested a Ticket. ALL %d Tickets go to the draw", available_tickets_members)

    # Read database!
    if filename:
        with open(filename, "rt") as csvfile:
            all_requesters = parse_participants_data(csvfile)
    else:
        all_requesters = parse_participants_data(StringIO(input_data, newline=''))

    logging.info("========================================================================")
    logging.info("Number of Tickets: %d (%d for members)", available_tickets, available_tickets_members)
    logging.info("========================================================================")
    logging.info("Lotto number: %d", winner_lotto)
    logging.info("========================================================================")

    if available_tickets_members >= len(all_requesters):
        logging.info("Congratulations!, all participants get a ticket (more tickets than participants...)")
        sys.exit(0)


    # Do the grouping:
    all_requesters = sorted(all_requesters, key=attrgetter('request_date'))
    waiting_list = [p for p in all_requesters if p.t == 'B']
    participants_g1 = [p for p in all_requesters if p.t == 'E']

    if len(waiting_list) > 0:
        logging.info("There are %d participants in the waiting list", len(waiting_list))
        for w in waiting_list:
            logging.info(f"{w.name}")




    print_all_participants(participants_g1)

    has_g2 = 10 <= (len(participants_g1) + (1 if board_request else 0))
    logging.info("========================================================================")
    logging.info("Participants: %d, Board Request: %s, Waiting List: %d", len(participants_g1), board_request, len(waiting_list))
    if has_g2:
        logging.info("========================================================================")
        winners_g2 = do_g2(participants_g1, available_tickets_members, winner_lotto)
    else:
        logging.info("Not enough requests. No G2")
        winners_g2 = []

    tickets_g1 = available_tickets_members - len(winners_g2)
    logging.info("========================================================================")
    winners_g1 = do_draw(participants_g1, winner_lotto, tickets_g1, "G1", winners_g2)

    winners = winners_g1 + winners_g2

    if len(winners) < available_tickets_members:
        logging.info("It seems that we have some extra tickets. The board decides!")

    logging.info("========================================================================")
    logging.info("========================================================================")
    logging.info("Congratulations to all winners!")
    for g, w in [("G2", winners_g2), ("G1", winners_g1)]:
        for p in w:
            logging.info("%s: %s", g, p)

def ask_input() -> str:
    data = ""

    line = ""
    print("Enter the content of CSV. Empty line to finish", flush=True)
    while line is not None:
        line = str(input())
        if len(line) > 0:
            data += line + os.linesep
        else:
            line = None

    return data


def ask_filename() -> str:
    """Ask the user to provide a filename and perform checks"""
    filename = None
    while filename is None:
        filename = str(input("Enter file input: "))

        if not os.path.isfile(filename):
            logging.error("'%s' is not a valid filename. Try again!")
            filename = None
    logging.debug("Input file: %s", filename)

    return filename


def ask_available_tickets() -> int:
    """Ask the user to provide number of available tickets and perform checks"""
    available_tickets = 0
    while available_tickets <= 0:
        available_tickets = int(input("Number of available tickets: "))

        if available_tickets <= 0:
            logging.error("Wrong number of available Tickets. Try again!")
    logging.debug("Available Tickets: %d", available_tickets)

    return available_tickets


def ask_board_request() -> bool:
    """Ask the user to answer a YES / NO question"""
    board_request = None
    board_request_valid_options = ("Y", "N")
    while board_request not in board_request_valid_options:
        board_request = str(input("Does the board require a ticket (Y/N): ")).upper()

        if board_request not in board_request_valid_options:
            logging.error("Wrong answer '%s'. Try again!", board_request)

    logging.debug("board request: %s", board_request)

    return board_request == "Y"


def ask_winner_lotto() -> int:
    winner_lotto = -1
    while winner_lotto < 0:
        try:
            winner_lotto = int(input("Enter the Lotto winner number: "))

            if winner_lotto < 0:
                raise ValueError
        except Exception:
            logging.error("Wrong winner number. Try again!")
            winner_lotto = -1

    logging.debug("Winner number: %d", winner_lotto)

    return winner_lotto


def parse_participants_data(data) -> List[Participant]:
    """Parse the participants data"""
    all_participants = []
    reader = csv.reader(data, delimiter=",")
    for i, row in enumerate(reader):
        try:
            if len(row) == 0:
                continue
            if len(row) < 5:
                raise ValueError
            d = f"{row[COL_DATE]} {row[COL_TIME]}"
            request_time = datetime.datetime.strptime(d, '%d/%m/%Y %H:%M')

            p = Participant(member_number=int(row[COL_NUM]),
                            name=row[COL_NAME],
                            request_date=request_time,
                            t=MembershipType(row[COL_TYPE]),
                            )

            # Add data of the participant to the participants_list
            all_participants.append(p)
            logging.debug("Participant added: %s", p)
        except Exception:
            logging.error("Somme issues in ROW %d. cannot add %s", i+1,row)
            sys.exit(-1)

    return all_participants


def print_all_participants(participants: List[Participant]):
    logging.info("The participants of the draw are (G1 group):")
    for i, p in enumerate(participants):
        logging.info(f"{i+1:3}. {p}")


def do_g2(all_participants, available_tickets_members, winner_lotto) -> List[Participant]:
    """Perform the draw for G2"""
    logging.info(
        "10 or more requests (including board). 20% of the tickets (min 1) will be assigned to 20% seniorest members (G2)!")

    # 20% of requests go to G2. Truncated!
    n_g2 = int(len(all_participants) * 0.2)
    logging.debug("PARTICIPANTS G2: 20% of PARTICIPANTS G1 (%d) = %d --> truncated to %d", len(all_participants),
                  len(all_participants) * 0.2,
                  n_g2)
    participants_g2 = list(sorted(all_participants, key=attrgetter('member_number')))[:n_g2]
    for p in participants_g2:
        logging.debug(p)

    if available_tickets_members <= 4:
        logging.info("TICKETS: 1 will go to G2 (4 or less tickets for members)")
        tickets_g2 = 1
    else:
        tickets_g2 = int(available_tickets_members * 0.2)
        logging.debug("TICKETS: 20% of %d (for members) = %d --> truncated to %d", available_tickets_members,
                      available_tickets_members * 0.2, tickets_g2)
    logging.info("TOTAL of %d tickets available for members (%d for G2, %d for G1)",
                 available_tickets_members, tickets_g2, available_tickets_members - tickets_g2)

    logging.info("Starting draw for G2...")

    return do_draw(participants_g2, winner_lotto, tickets_g2, "G2")


def do_draw(participants: List[Participant], winner_lotto: int, number_tickets: int, group: str, exclude = []) -> List[Participant]:
    logging.info("%d participants for %d tickets in %s", len(participants), number_tickets, group)

    for i, p in enumerate(participants):
        if p in exclude:
            logging.info(f"{group}: {i + 1:3}. {p} ***** EXCLUDED *****")
        else:
            logging.info(f"{group}: {i + 1:3}. {p}")

    winner_draw = winner_lotto % len(participants)
    division_res = int(winner_lotto / len(participants))
    logging.info("%s BPB-draw winner is: %d (Lotto winner/#participants = %d/%d = %d.x, Remainder=%d)",
                 group, winner_draw, winner_lotto, len(participants), division_res, winner_draw)
    if winner_draw == 0:
        logging.info("Remainder 0. Last request wins: %d", len(participants))
        start_idx = len(participants) - 1
    else:
        # python does indexing starting with 0, so substract 1 to the winner (-1 is equal to last)
        start_idx = winner_draw -1

    logging.info(f"And the winner(s) of {group} is/are...")
    assigned_tickets = 0
    winners = []
    for idx in range(start_idx, len(participants)):
        p = participants[idx]
        if p not in exclude:
            assigned_tickets += 1
            logging.info(f"{idx+1:3}. {p.name}")
            winners.append(p)
        else:
            logging.info(f"--> excluding {idx+1:3}. {p.name} <--")

        if assigned_tickets == number_tickets:
            logging.info(f"All tickets assigned in {group}!")
            break

    if assigned_tickets < number_tickets:
        # continue with the beginning of the list
        for idx in range(0, start_idx):
            p = participants[idx]
            if p not in exclude:
                assigned_tickets += 1
                logging.info(f"{idx + 1:3}. {p.name}")
                winners.append(p)
            else:
                logging.info(f"--> excluding {idx+1:3}. {p.name} <--")

            if assigned_tickets == number_tickets:
                logging.info("All tickets assigned in %s!", group)
                break

    logging.info("Draw finished for %s", group)

    return winners


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    filename = None
    if len(sys.argv) > 1:
        filename = sys.argv[1]

    main(filename)
