(define (domain snake)
(:requirements :strips :negative-preconditions :equality)
(:constants
    dummypoint
)
(:predicates
    (ISADJACENT ?x ?y)
    (tailsnake ?x)
    (headsnake ?x)
    (nextsnake ?x ?y)
    (blocked ?x)
    (spawn ?x)
    (NEXTSPAWN ?x ?y)
    (ispoint ?x)
)
(:action move
    :parameters (?head ?newhead ?tail ?newtail)
    :precondition
    (and
        (headsnake ?head)
        (tailsnake ?tail)
        (nextsnake ?newtail ?tail)
        (ISADJACENT ?head ?newhead)
        (not (blocked ?newhead))
        (not (ispoint ?newhead))
    )
    :effect
    (and
        (not (headsnake ?head))
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (not (tailsnake ?tail))
        (not (nextsnake ?newtail ?tail))
        (tailsnake ?newtail)
        (blocked ?newhead)
        (not (blocked ?tail))
    )
)
(:action move-and-eat-spawn
    :parameters (?head ?newhead ?spawnpoint ?nextspawnpoint)
    :precondition
    (and
        (headsnake ?head)
        (spawn ?spawnpoint)
        (NEXTSPAWN ?spawnpoint ?nextspawnpoint)
        (ISADJACENT ?head ?newhead)
        (ispoint ?newhead)
        (not (blocked ?newhead))
        (not (= ?spawnpoint dummypoint))
    )
    :effect
    (and
        (not (headsnake ?head))
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (blocked ?newhead)
        (not (ispoint ?newhead))
        (not (spawn ?spawnpoint))
        (ispoint ?spawnpoint)
        (spawn ?nextspawnpoint)
    )
)
(:action move-and-eat-no-spawn
    :parameters (?head ?newhead)
    :precondition
    (and
        (headsnake ?head)
        (spawn dummypoint)
        (ISADJACENT ?head ?newhead)
        (ispoint ?newhead)
        (not (blocked ?newhead))
    )
    :effect
    (and
        (not (headsnake ?head))
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (blocked ?newhead)
        (not (ispoint ?newhead))
    )
)
)