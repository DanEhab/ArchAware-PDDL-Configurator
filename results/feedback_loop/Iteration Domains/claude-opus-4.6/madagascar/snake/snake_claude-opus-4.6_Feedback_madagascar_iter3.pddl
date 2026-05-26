(define (domain snake)
(:requirements :strips :negative-preconditions :equality)
(:constants
    dummypoint
)
(:predicates
    (ispoint ?x)
    (spawn ?x)
    (headsnake ?x)
    (tailsnake ?x)
    (nextsnake ?x ?y)
    (blocked ?x)
    (ISADJACENT ?x ?y)
    (NEXTSPAWN ?x ?y)
)
(:action move-and-eat-no-spawn
    :parameters (?head ?newhead)
    :precondition
    (and
        (headsnake ?head)
        (ISADJACENT ?head ?newhead)
        (ispoint ?newhead)
        (spawn dummypoint)
        (not (blocked ?newhead))
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
(:action move-and-eat-spawn
    :parameters (?head ?newhead ?spawnpoint ?nextspawnpoint)
    :precondition
    (and
        (headsnake ?head)
        (ISADJACENT ?head ?newhead)
        (ispoint ?newhead)
        (spawn ?spawnpoint)
        (NEXTSPAWN ?spawnpoint ?nextspawnpoint)
        (not (= ?spawnpoint dummypoint))
        (not (blocked ?newhead))
    )
    :effect
    (and
        (ispoint ?spawnpoint)
        (spawn ?nextspawnpoint)
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (blocked ?newhead)
        (not (spawn ?spawnpoint))
        (not (ispoint ?newhead))
        (not (headsnake ?head))
    )
)
(:action move
    :parameters (?head ?newhead ?tail ?newtail)
    :precondition
    (and
        (headsnake ?head)
        (ISADJACENT ?head ?newhead)
        (tailsnake ?tail)
        (nextsnake ?newtail ?tail)
        (not (blocked ?newhead))
        (not (ispoint ?newhead))
    )
    :effect
    (and
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (blocked ?newhead)
        (tailsnake ?newtail)
        (not (headsnake ?head))
        (not (tailsnake ?tail))
        (not (blocked ?tail))
        (not (nextsnake ?newtail ?tail))
    )
)
)