(define (domain snake)
(:requirements :strips :negative-preconditions :equality)
(:constants
    dummypoint
)
(:predicates
    (tailsnake ?x)
    (headsnake ?x)
    (blocked ?x)
    (spawn ?x)
    (ispoint ?x)
    (ISADJACENT ?x ?y)
    (nextsnake ?x ?y)
    (NEXTSPAWN ?x ?y)
)
(:action move
    :parameters (?head ?newhead ?tail ?newtail)
    :precondition
    (and
        (headsnake ?head)
        (ISADJACENT ?head ?newhead)
        (not (blocked ?newhead))
        (not (ispoint ?newhead))
        (tailsnake ?tail)
        (nextsnake ?newtail ?tail)
    )
    :effect
    (and
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (not (headsnake ?head))
        (not (nextsnake ?newtail ?tail))
        (tailsnake ?newtail)
        (blocked ?newhead)
        (not (blocked ?tail))
        (not (tailsnake ?tail))
    )
)

(:action move-and-eat-no-spawn
    :parameters (?head ?newhead)
    :precondition
    (and
        (headsnake ?head)
        (ISADJACENT ?head ?newhead)
        (not (blocked ?newhead))
        (ispoint ?newhead)
        (spawn dummypoint)
    )
    :effect
    (and
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (not (headsnake ?head))
        (blocked ?newhead)
        (not (ispoint ?newhead))
    )
)

(:action move-and-eat-spawn
    :parameters (?head ?newhead ?spawnpoint ?nextspawnpoint)
    :precondition
    (and
        (headsnake ?head)
        (ISADJACENT ?head ?newhead)
        (not (blocked ?newhead))
        (ispoint ?newhead)
        (spawn ?spawnpoint)
        (NEXTSPAWN ?spawnpoint ?nextspawnpoint)
        (not (= ?spawnpoint dummypoint))
    )
    :effect
    (and
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (not (headsnake ?head))
        (blocked ?newhead)
        (not (ispoint ?newhead))
        (ispoint ?spawnpoint)
        (not (spawn ?spawnpoint))
        (spawn ?nextspawnpoint)
    )
)

)