(define (domain snake)
(:requirements :strips :negative-preconditions :equality)
(:constants
    dummypoint
)
(:predicates
    (headsnake ?x)
    (tailsnake ?x)
    (nextsnake ?x ?y)
    (blocked ?x)
    (ispoint ?x)
    (spawn ?x)
    (NEXTSPAWN ?x ?y)
    (ISADJACENT ?x ?y)
)
(:action move
    :parameters (?head ?newhead ?tail ?newtail)
    :precondition
    (and
        (headsnake ?head)
        (not (blocked ?newhead))
        (not (ispoint ?newhead))
        (tailsnake ?tail)
        (nextsnake ?newtail ?tail)
        (ISADJACENT ?head ?newhead)
    )
    :effect
    (and
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (blocked ?newhead)
        (tailsnake ?newtail)
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
        (not (blocked ?newhead))
        (spawn ?spawnpoint)
        (not (= ?spawnpoint dummypoint))
        (NEXTSPAWN ?spawnpoint ?nextspawnpoint)
        (ISADJACENT ?head ?newhead)
    )
    :effect
    (and
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (blocked ?newhead)
        (not (headsnake ?head))
        (not (ispoint ?newhead))
        (spawn ?nextspawnpoint)
        (not (spawn ?spawnpoint))
        (ispoint ?spawnpoint)
    )
)
(:action move-and-eat-no-spawn
    :parameters (?head ?newhead)
    :precondition
    (and
        (headsnake ?head)
        (ispoint ?newhead)
        (not (blocked ?newhead))
        (spawn dummypoint)
        (ISADJACENT ?head ?newhead)
    )
    :effect
    (and
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (blocked ?newhead)
        (not (headsnake ?head))
        (not (ispoint ?newhead))
    )
)
)