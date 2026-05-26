(define (domain snake)
(:requirements :strips :negative-preconditions :equality)
(:constants
    dummypoint
)
(:predicates
    (ispoint ?x)
    (blocked ?x)
    (spawn ?x)
    (headsnake ?x)
    (tailsnake ?x)
    (nextsnake ?x ?y)
    (NEXTSPAWN ?x ?y)
    (ISADJACENT ?x ?y)
)
(:action move-and-eat-no-spawn
    :parameters (?newhead ?head)
    :precondition
    (and
        (ispoint ?newhead)
        (not (blocked ?newhead))
        (ISADJACENT ?head ?newhead)
        (headsnake ?head)
        (spawn dummypoint)
    )
    :effect
    (and
        (not (ispoint ?newhead))
        (blocked ?newhead)
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (not (headsnake ?head))
    )
)
(:action move-and-eat-spawn
    :parameters (?newhead ?head ?spawnpoint ?nextspawnpoint)
    :precondition
    (and
        (ispoint ?newhead)
        (not (blocked ?newhead))
        (ISADJACENT ?head ?newhead)
        (headsnake ?head)
        (not (= ?spawnpoint dummypoint))
        (spawn ?spawnpoint)
        (NEXTSPAWN ?spawnpoint ?nextspawnpoint)
    )
    :effect
    (and
        (not (ispoint ?newhead))
        (blocked ?newhead)
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (not (headsnake ?head))
        (ispoint ?spawnpoint)
        (not (spawn ?spawnpoint))
        (spawn ?nextspawnpoint)
    )
)
(:action move
    :parameters (?newhead ?head ?tail ?newtail)
    :precondition
    (and
        (not (blocked ?newhead))
        (not (ispoint ?newhead))
        (ISADJACENT ?head ?newhead)
        (headsnake ?head)
        (tailsnake ?tail)
        (nextsnake ?newtail ?tail)
    )
    :effect
    (and
        (blocked ?newhead)
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (not (headsnake ?head))
        (tailsnake ?newtail)
        (not (tailsnake ?tail))
        (not (blocked ?tail))
        (not (nextsnake ?newtail ?tail))
    )
)
)