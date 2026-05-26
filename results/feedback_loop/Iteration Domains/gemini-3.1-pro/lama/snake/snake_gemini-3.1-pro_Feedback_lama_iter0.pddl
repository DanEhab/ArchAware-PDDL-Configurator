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
    (ISADJACENT ?x ?y)
    (NEXTSPAWN ?x ?y)
)

(:action move-and-eat-no-spawn
    :parameters (?head ?newhead)
    :precondition
    (and
        (ISADJACENT ?head ?newhead)
        (headsnake ?head)
        (ispoint ?newhead)
        (spawn dummypoint)
        (not (blocked ?newhead))
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

(:action move
    :parameters (?head ?newhead ?tail ?newtail)
    :precondition
    (and
        (ISADJACENT ?head ?newhead)
        (headsnake ?head)
        (tailsnake ?tail)
        (nextsnake ?newtail ?tail)
        (not (blocked ?newhead))
        (not (ispoint ?newhead))
    )
    :effect
    (and
        (headsnake ?newhead)
        (tailsnake ?newtail)
        (nextsnake ?newhead ?head)
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
        (ISADJACENT ?head ?newhead)
        (NEXTSPAWN ?spawnpoint ?nextspawnpoint)
        (not (= ?spawnpoint dummypoint))
        (headsnake ?head)
        (ispoint ?newhead)
        (spawn ?spawnpoint)
        (not (blocked ?newhead))
    )
    :effect
    (and
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (blocked ?newhead)
        (ispoint ?spawnpoint)
        (spawn ?nextspawnpoint)
        (not (headsnake ?head))
        (not (ispoint ?newhead))
        (not (spawn ?spawnpoint))
    )
)
)