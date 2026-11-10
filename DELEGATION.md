# Delegation Boundary

## Klassifikation der Aktionen

Pro Aktion genau eine Entscheidung: `alone` oder `approval`.

| # | Action | Decision (alone / approval) | Justification |
|---|--------|-----------------------------|---------------|
| 1 | Read the appointments of a day | alone | read only|
| 2 | Look up the weather | alone | read only |
| 3 | Search train connections | alone | as long that's our only possibility for transits |
| 4 | Read notes | alone | read only |
| 5 | Create a personal block in the calendar (e.g. travel time, no other attendees) | alone | is derived from the booking |
| 6 | Reschedule an appointment with other attendees | approval | Does it make sense to reschedule that particular appointment? |
| 7 | Book a train ticket | approval | can affect other appointments and in this case the user should make the decision, how to deal with the situation |
| 8 | Send a message to third parties | approval | the necessity and content of a message depend on the appointment, but asking for approval for each meassage can be annoying |
| 9 | Create a note | approval | notes are the database for future planning and therefore it has to be correct |
| 10 | Delete a note | approval | unshure if I'll still need a note of a already passed appointment |

## My rule
user has full controll and therefore only read only actions are allowed to be executed without approval


## Observations from the role play

1. In the promt wasn't asked for collision. Should the agent check or inform about collisions anyway?
2. How far ahead does the agent think? How does he handle the decision when there is a scheduling conflict after a decision has been made: Does he suggest informing the participants of the meeting that was rejected, or does he suggest scheduling a new meeting?
3. How is quantitative data converted into answers? For example, a rainfall probability of 0.6 → rain: yes or no?
