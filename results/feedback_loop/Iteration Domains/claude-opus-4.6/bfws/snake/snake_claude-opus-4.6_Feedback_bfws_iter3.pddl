(define (domain snake)
(:requirements :strips :negative-preconditions :equality)
(:constants
    dummypoint
)
(:predicates
    (spawn ?x)
    (ispoint ?x)
    (headsnake ?x)
    (tailsnake ?x)
    (nextsnake ?x ?y)
    (blocked ?x)
    (NEXTSPAWN ?x ?y)
    (ISADJACENT ?x ?y)
)
(:action move
    :parameters (?head ?newhead ?tail ?newtail)
    :precondition
    (and
        (headsnake ?head)
        (tailsnake ?tail)
        (nextsnake ?newtail ?tail)
        (not (blocked ?newhead))
        (not (ispoint ?newhead))
        (ISADJACENT ?head ?newhead)
    )
    :effect
    (and
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (tailsnake ?newtail)
        (blocked ?newhead)
        (not (headsnake ?head))
        (not (tailsnake ?tail))
        (not (nextsnake ?newtail ?tail))
        (not (blocked ?tail))
    )
)
(:action move-and-eat-spawn
    :parameters (?head ?newhead ?spawnpoint ?nextspawnpoint)
    :precondition
    (and
        (headsnake ?head)
        (ispoint ?newhead)
        (spawn ?spawnpoint)
        (not (= ?spawnpoint dummypoint))
        (not (blocked ?newhead))
        (NEXTSPAWN ?spawnpoint ?nextspawnpoint)
        (ISADJACENT ?head ?newhead)
    )
    :effect
    (and
        (spawn ?nextspawnpoint)
        (ispoint ?spawnpoint)
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (blocked ?newhead)
        (not (ispoint ?newhead))
        (not (spawn ?spawnpoint))
        (not (headsnake ?head))
    )
)
(:action move-and-eat-no-spawn
    :parameters (?head ?newhead)
    :precondition
    (and
        (headsnake ?head)
        (ispoint ?newhead)
        (spawn dummypoint)
        (not (blocked ?newhead))
        (ISADJACENT ?head ?newhead)
    )
    :effect
    (and
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (blocked ?newhead)
        (not (ispoint ?newhead))
        (not (headsnake ?head))
    )
)
)