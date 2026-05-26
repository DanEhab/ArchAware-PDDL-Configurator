(define (domain Depot)
(:requirements :strips :typing)
(:types place locatable - object
	depot distributor - place
        truck hoist surface - locatable
        pallet crate - surface)

(:predicates (available ?x - hoist) 
             (clear ?x - surface)
             (on ?x - crate ?y - surface)
             (in ?x - crate ?y - truck)
             (lifting ?x - hoist ?y - crate)
             (at ?x - locatable ?y - place))

(:action Drive
:parameters (?x - truck ?y - place ?z - place) 
:precondition (and (at ?x ?y))
:effect (and (not (at ?x ?y)) (at ?x ?z)))

(:action Load
:parameters (?x - hoist ?y - crate ?z - truck ?p - place)
:precondition (and (lifting ?x ?y) (at ?z ?p) (at ?x ?p))
:effect (and (not (lifting ?x ?y)) (in ?y ?z) (available ?x)))

(:action Unload 
:parameters (?x - hoist ?y - crate ?z - truck ?p - place)
:precondition (and (in ?y ?z) (available ?x) (at ?z ?p) (at ?x ?p))
:effect (and (lifting ?x ?y) (not (in ?y ?z)) (not (available ?x))))

(:action Lift
:parameters (?x - hoist ?y - crate ?z - surface ?p - place)
:precondition (and (clear ?y) (on ?y ?z) (available ?x) (at ?y ?p) (at ?x ?p))
:effect (and (lifting ?x ?y) (not (clear ?y)) (not (on ?y ?z)) (clear ?z) (not (available ?x)) (not (at ?y ?p))))

(:action Drop 
:parameters (?x - hoist ?y - crate ?z - surface ?p - place)
:precondition (and (lifting ?x ?y) (clear ?z) (at ?z ?p) (at ?x ?p))
:effect (and (not (lifting ?x ?y)) (clear ?y) (on ?y ?z) (not (clear ?z)) (available ?x) (at ?y ?p)))
)