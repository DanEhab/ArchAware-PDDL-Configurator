(define (domain Depot)
(:requirements :strips :typing)
(:types place locatable - object
	depot distributor - place
        truck hoist surface - locatable
        pallet crate - surface)

(:predicates (on ?x - crate ?y - surface)
             (in ?x - crate ?y - truck)
             (clear ?x - surface)
             (at ?x - locatable ?y - place)
             (lifting ?x - hoist ?y - crate)
             (available ?x - hoist))

(:action Drop 
:parameters (?x - hoist ?y - crate ?z - surface ?p - place)
:precondition (and (clear ?z) (lifting ?x ?y) (at ?z ?p) (at ?x ?p))
:effect (and (on ?y ?z) (clear ?y) (at ?y ?p) (available ?x) (not (clear ?z)) (not (lifting ?x ?y))))

(:action Unload 
:parameters (?x - hoist ?y - crate ?z - truck ?p - place)
:precondition (and (in ?y ?z) (available ?x) (at ?z ?p) (at ?x ?p))
:effect (and (lifting ?x ?y) (not (in ?y ?z)) (not (available ?x))))

(:action Load
:parameters (?x - hoist ?y - crate ?z - truck ?p - place)
:precondition (and (lifting ?x ?y) (at ?z ?p) (at ?x ?p))
:effect (and (in ?y ?z) (available ?x) (not (lifting ?x ?y))))

(:action Lift
:parameters (?x - hoist ?y - crate ?z - surface ?p - place)
:precondition (and (on ?y ?z) (clear ?y) (available ?x) (at ?y ?p) (at ?x ?p))
:effect (and (clear ?z) (lifting ?x ?y) (not (on ?y ?z)) (not (clear ?y)) (not (at ?y ?p)) (not (available ?x))))

(:action Drive
:parameters (?x - truck ?y - place ?z - place) 
:precondition (and (at ?x ?y))
:effect (and (at ?x ?z) (not (at ?x ?y))))
)