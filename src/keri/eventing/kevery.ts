


// Kevery processes an incoming message stream and when appropriate generates
// an outgoing steam. When the incoming streams includes key event messages
// then Kevery acts putKes Kever (KERI key event verifier) factory.

const { Serder } = require('../core/serder')
const derivationCodes = require('../core/derivationCode&Length')
const { Prefixer } = require('../core/prefixer')
const { Kever } = require('../eventing/Kever')
const { CryCounter } = require('../core/cryCounter')
const {Sigcounter} = require('../core/SigCounter')
const {Sigver} = require('../core/sigver')
const {Siger} = require('../core/siger')
const { Serials, Versionage, IcpLabels, Ilks } = require('../core/core')
// const {SealEvent} = require('../eventing/util')
const _ = require('lodash');
import { range } from "lodash";
const { Verfer } = require("../core/verfer");
const { snkey, Logger, dgkey } = require('../db/index')
// Only supports current version VERSION

// Has the following public attributes and properties:

// Attributes:
// .ims is bytearray incoming message stream
// .oms is bytearray outgoing message stream
// .kevers is dict of existing kevers indexed by pre (qb64) of each Kever
// .logs is named tuple of logs
// .framed is Boolean stream is packet framed If True Else not framed
class Kevery {
    framed: any;
    ims: any;
    kevers: any;
    logger: any;
    logger_: any;
    oms: any;


    constructor(ims = null, oms = null, kevers = null, logger = null, framed = true) {

        if (ims) { this.ims = ims } else {
            this.ims =  Buffer.alloc(256);
        }

        if (oms) { this.oms = oms } else {
            this.oms =  Buffer.alloc(256);
        }

        if (framed) { this.framed = true } else {
            this.framed = false
        }

        if (kevers) { this.kevers = kevers } else {
            this.kevers = {}
        }

        if (!logger) { 
            
            this.logger_= new Logger().next().value
        }
        else {
            this.logger = logger
        }

    }


    /**
 * @description  Process all messages from incoming message stream, ims, when provided
Otherwise process all messages from .ims
 */
    processAll(ims = null) {
        
    if (ims) {
        // @ts-expect-error ts-migrate(2358) FIXME: The left-hand side of an 'instanceof' expression m... Remove this comment to see the full error message
        if (!(ims instanceof Buffer)) {
            // @ts-expect-error ts-migrate(2322) FIXME: Type 'Buffer' is not assignable to type 'null'.
            ims = Buffer.from(ims,'binary')
        } 
    }
    else {
        ims = this.ims
    }
    let ims_ = [ims]
           for (let i = 0 ; i < ims_.length ; i ++) {
            try {
               
         this.processOne(ims_[i], this.framed,true)
            } catch (error) {
                console.log("\nERROR:",error)
                throw error
            }
        }
}


    /**
     * @description Extract one msg with attached signatures from incoming message stream, ims
    And dispatch processing of message
     * @param {*} ims ims is bytearray of serialized incoming message stream.
                May contain one or more sets each of a serialized message with
                attached cryptographic material such as signatures or receipts.
 
    * @param {*} framed framed is Boolean, If True and no sig counter then extract signatures
                        until end-of-stream. This is useful for framed packets with
                         one event and one set of attached signatures per invocation.
     */
    async processOne(ims: any, framed = true,flag = false) {
         let serder, nsigs ,counter = null
         let sigers = []

         try {
             serder = new Serder(ims)
             let raw = serder.raw()
             serder.set_raw(raw)
         } catch (err) {
             throw new Error(`Error while processing message stream = ${err}`);
         }

         let version = serder.version()
         
         if (!_.isEqual(version, Versionage)) {
             throw new Error(`Unsupported version = ${version}, expected ${Versionage}.`)
         }
         ims =  ims.slice(serder.size(),ims.length)
         let ilk = serder.ked()['ilk']  //# dispatch abased on ilk (Types of events)
         let arr = [Ilks.icp, Ilks.rot, Ilks.ixn, Ilks.dip, Ilks.drt]
         if (arr.includes(ilk)) {

             try {
                 counter = new Sigcounter(null, ims)
                 nsigs = counter.count()
                 ims = ims.slice((counter.qb64()).length, ims.length)
             } catch (error) {
                 console.log("ERROR WHILE EXTRACTING SIGNATURES :",error)
                 nsigs = 0
             }

             // let sigers = []

             if (nsigs) {
                 for (let i in range(nsigs)) {
                     //  # check here for type of attached signatures qb64 or qb2
                     let  args = [null,null,null,derivationCodes.SigTwoCodex.Ed25519,0,ims]
                    var siger = new Siger(null,...args)
                    siger.setVerfer(siger.verfer())
                     sigers.push(siger)
                     
                     ims =  ims.slice(0, (siger.qb64()).length)
                 }
             }
             else {  //  iF THERE IS no info on attached sigs
                 if (framed) {   //parse for signatures until end-of-stream
                     while (ims) {
                         let  args = [null,null,null,derivationCodes.SigTwoCodex.Ed25519,0,ims]
                         siger = new Siger(null,...args)
                         sigers.push(siger)
                         ims =  ims.slice(0, (siger.qb64()).length)
                     }
                 }
             }

             if (!sigers) {
                 throw new Error(`Missing attached signature(s).`);
             }
           this.processEvent(serder, sigers,flag)

         } else if (ilk === Ilks.rct) {
             try {
                 let counter = new CryCounter(null,ims)  //# qb64
                 let ncpts = counter.count()
                 ims = ims.slice(0, (counter.qb64()).length)
             } catch (error) {
                 let ncpts = 0
             }

             // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'ncpts'.
             if (ncpts) {
                 // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'ncpts'.
                 for (let i in range(ncpts)) {
                     let verfer = new Verfer(null,ims)
                     ims  =  ims.slice(0, (verfer.qb64()).length)
                     // @ts-expect-error ts-migrate(2552) FIXME: Cannot find name 'derivation_code'. Did you mean '... Remove this comment to see the full error message
                     let sigver = new Sigver(null,derivation_code.twoCharCode.Ed25519,verfer,0,)
                     // @ts-expect-error ts-migrate(2552) FIXME: Cannot find name 'sigvers'. Did you mean 'sigver'?
                     sigvers.push(sigver)
                     ims =  ims.slice(0, (verfer.qb64()).length)
                 }
             } else {
                 if (framed) {
                     while (ims) {
                         let verfer = new Verfer(ims)
                         ims = ims.slice(0, (verfer.qb64()).length)

                         let sigver = new Sigver(ims, verfer)
                         // @ts-expect-error ts-migrate(2552) FIXME: Cannot find name 'sigvers'. Did you mean 'sigver'?
                         sigvers.push(sigver)

                         ims =  ims.slice(0, (sigver.qb64()).length)
                     }
                 }
             }

             // @ts-expect-error ts-migrate(2552) FIXME: Cannot find name 'sigvers'. Did you mean 'sigers'?
             if (!sigvers)
                 throw new Error(`Missing attached receipt couplet(s).`);

             // @ts-expect-error ts-migrate(2552) FIXME: Cannot find name 'sigvers'. Did you mean 'sigers'?
             await this.processReceipt(serder, sigvers)


         } else if (ilk === Ilks.vrc) {
             let nsigs = null
             try {
                counter = new Sigcounter(null, ims,null,null,derivationCodes.SigCntCodex.Base64)  //# qb64
                 nsigs = counter.count()
                 
                 ims = ims.slice((counter.qb64()).length, ims.length)
             } catch (error) {
                 console.log("Error :",error)
                 nsigs = 0
             }

             if (nsigs) {

                 for (let i in range(nsigs)) {
                     let  args = [null,null,null,derivationCodes.SigTwoCodex.Ed25519,0,ims]
                     let siger = new Siger(null,...args)
                     
                     siger.setVerfer(siger.verfer())
                     sigers.push(siger)
                     ims = ims.slice(0, (siger.qb64()).length)
                 }
             }   else {
                 if (framed) {
                     while (ims) {
                         let  args = [null,null,null,derivationCodes.SigTwoCodex.Ed25519,0,ims]
                        let siger = new Siger(null,...args)
                         sigers.push(siger)
                         ims = ims.slice(0, (siger.qb64()).length)
                     }
                 }
             }

             if (!sigers) {
                 throw new Error(`Missing attached signature(s) to receipt.`)
             }
             this.processChit(serder, sigers)
         } else {
             throw new Error(`Unexpected message ilk = ${ilk}.`);
         }
     }


    /**
     * @description Process one event serder with attached indexd signatures sigers
     * Receipt dict labels
            vs  # version string
            pre  # qb64 prefix
            ilk  # rct
            dig  # qb64 digest of receipted event
     */
    async  processEvent(serder: any, sigers: any,flag: any) {
          let prefixer, dig, kever, dgkey_, sno = null
          let signers: any = []
          let signers_icp: any = []
          let ked = serder.ked()
          serder.set_ked(ked)
          var date = new Date()

          try {
              prefixer = new Prefixer(null, derivationCodes.oneCharCode.Ed25519N, null, null, null, ked["pre"])
          } catch (error) {
              throw new Error(`Invalid pre = ${ked["pre"]}.`);

          }

          let pre = prefixer.qb64()
          let ilk = ked["ilk"]

          let sn = ked['sn']
          if (sn.length > 32) {
              throw new Error(`Invalid sn = ${sn} too large.`)
          }

          try {
              sn = parseInt(sn, 16)
          } catch (error) {
              throw new Error(`Invalid sn = ${sn}`);
          }

          dig = serder.dig()


          if (!(pre in this.kevers)) {
              if (ilk == Ilks.icp) {

                  kever =   new Kever(serder,sigers, null,this.logger,flag)
                  
                  this.kevers[pre] = kever
              } else {
                  dgkey_ = dgkey(pre, dig)
                      this.logger.putDts(dgkey_, Buffer.from(date.toISOString(),'binary'))
                  for(let siger in sigers){
                      signers[siger] = sigers[siger].qb64b()
                  }


                    this.logger.putSigs(dgkey_,signers)
                     this.logger.putEvt(dgkey_, serder.raw())
                    this.logger.addOoe(snkey(pre, sn), dig)
              }
          } 
          else {
              if (ilk == Ilks.icp) { 
                  dgkey_ = dgkey(pre, dig)
                  this.logger.putDts(dgkey_, Buffer.from(date.toISOString(),'binary'))
                  for(let siger in sigers){
                      signers_icp[siger] = sigers[siger].qb64b()
                  }
                   this.logger.putSigs(dgkey_, signers_icp)
                  this.logger.putEvt(dgkey_, serder.raw())
                  this.logger.addLde(snkey(pre, sn), dig)
              } else {
                  kever = this.kevers[pre] // # get existing kever for pre
                  sno = kever.sn + 1  //# proper sn of new inorder event
                  if (sn > sno)           //  # sn later than sno so out of order escrow
                  {
                      dgkey_ = dgkey(pre, dig)
                      this.logger.putDts(dgkey_, Buffer.from(date.toISOString(),'binary'))

                      for(let siger in sigers){
                          signers[siger] =   sigers[siger].qb64b()
                      }
                      this.logger.putSigs(dgkey_, signers)
                      this.logger.putEvt(dgkey_, serder.raw())
                      this.logger.addOoe(snkey(pre, sn), dig)
                  } else if ((sn == sno) ||
                      (ilk == Ilks.rot && kever.lastEst.sn < sn <= sno)) {
                      kever.update(serder, sigers,null,null,flag)

                  } else {
                      dgkey_= dgkey(pre, dig)
                      this.logger.putDts(dgkey_, Buffer.from(date.toISOString(),'binary'))

                      for(let siger in sigers){
                          signers[siger] =   sigers[siger].qb64b()
                      }
                      this.logger.putSigs(dgkey_,signers)
                      this.logger.putEvt(dgkey_, serder.raw())
                      this.logger.addLde(snkey(pre, sn), dig)
                  }
              }


          }

      }



    /**
     * @description  Process one receipt serder with attached sigvers
     * @param {*} serder 
     * @param {*} sigvers 
     */
    async    processReceipt(serder: any, sigvers: any){

           let ked = serder.ked()
           let pre = ked["pre"]
           let  sn = ked["sn"]
                let dig,snkey,ldig,eserder,couplet = null
           if(sn.length > 32){
            throw new Error(`Invalid sn = ${sn} too large.`)
           }
           try{
            sn = parseInt(sn,16)
        }catch(error){
            throw new Error(`Invalid sn = ${sn}`)
        }

        dig = ked["dig"]
       // # Only accept receipt if for last seen version of event at sn
        // @ts-expect-error ts-migrate(2722) FIXME: Cannot invoke an object which is possibly 'undefin... Remove this comment to see the full error message
        snkey = await snkey(pre, sn)
        ldig = await this.logger.getKeLast(snkey)   // retrieve dig of last event at sn.


      //  # retrieve event by dig
      // @ts-expect-error ts-migrate(2552) FIXME: Cannot find name 'dgKey'. Did you mean 'dgkey_'?
      let  dgkey_ =  dgKey(pre, dig)
        let raw = (self as any).logger.getEvt(dgkey_); //# retrieve receipted event at dig
    //# retrieve receipted event at dig

        if(ldig){

            ldig = ldig.toString('utf-8')
            if(ldig !== dig){
                throw new Error(`Stale receipt at sn = ${ked["sn"]}`)
            }

            eserder =  new Serder(Buffer.from(raw,'binary')) 

            for(let sigver of sigvers) {
                if(!sigver.verfer.nontrans){
                    {}
                }
                if(sigver.verfer.verify(sigver.raw(), eserder.raw())){
                    couplet = sigver.verfer.qb64b() + sigver.qb64b()
                        this.logger.addRct(dgkey, couplet)
                }

            }
        }else {
            if(raw){

                throw new Error(`Bad receipt for sn = ${ked["sn"]} and dig = ${dig }.`)
            }

            for(let sigver of sigvers){
                if(!sigver.verfer.nontrans){
                    {}
                }
                // @ts-expect-error ts-migrate(2532) FIXME: Object is possibly 'undefined'.
                if(sigver.verfer.verify(sigver.raw(), eserder.raw())){

                    couplet = sigver.verfer.qb64b() + sigver.qb64b()
                        this.logger.addUre(dgkey, couplet)
                }

            }
        }
        }



    /**
     * @description  Process one transferable validator receipt (chit) serder with attached sigers
     * @param {} serder serder is chit serder (transferable validator receipt message)
     * @param {*} sigers    sigers is list of Siger instances that contain signature

     */
    processChit(serder: any, sigers: any){
        let SealEvent = {pre:"" ,dig: ""}
            let dig,seal,sealet,snKey_,dgKey_,ldig,raw,rekever,triplet = null
       let ked = serder.ked()
       serder.set_ked(ked)
       
        // serder.set_raw(serder.raw())
       let pre = ked["pre"]
       let  sn = ked["sn"]

       if(sn.length > 32){
           throw new Error(`Invalid sn = ${sn} too large.`);
       }

       try{
           sn = parseInt(sn,16)
       }catch(error){
           throw new Error(`Invalid sn = ${sn}`)
       }
       dig = ked["dig"]
        SealEvent.pre = ked["seal"].pre
        SealEvent.dig = ked["seal"].dig
        // seal = SealEvent
       sealet = [Buffer.from(SealEvent.pre,'binary'), Buffer.from(SealEvent.dig,'binary')]
       sealet = Buffer.concat(sealet)

       snKey_ = snkey(pre,sn)
       ldig = this.logger.getKeLast(snKey_)  // # retrieve dig of last event at sn
       dgKey_ = dgkey(pre,dig)
       raw = this.logger.getEvt(dgKey_) // # retrieve receipted event at dig    
       if(ldig != null && ldig !== false ){

           ldig = ldig.toString()
        if((ldig !== dig)){
            throw new Error(`Stale receipt at sn = ${dig}, ${ldig} ${ked["seal"].dig}`)
           }
       }
       else {
        if(raw !=null){
            throw new Error(`Bad receipt for sn = ${ked["sn"]} and dig = ${dig}.`)
        }

       }



    if (ldig != null && raw !=null && SealEvent.pre in this.kevers){
        rekever = this.kevers[SealEvent.pre]

        if (rekever.lastEst.dig !== SealEvent.dig)
        throw new Error(`Stale receipt for pre = ${SealEvent.pre} dig = ${SealEvent.dig} from validator = ${SealEvent.pre}.`);
    
       
        for (let siger in sigers ){
            if(sigers[siger].index() >=(rekever.verfers).length){
                throw new Error(`Index = ${sigers[siger].index} to large for keys.`)
            }
            sigers[siger].setVerfer(rekever.verfers[sigers[siger].index()] )
            if(sigers[siger].verfer().verify(sigers[siger].raw(), raw)){
                triplet = [sealet , sigers[siger].qb64b()]
                triplet = Buffer.concat(triplet)
                    this.logger.addVrc(dgKey_,triplet)
            }
        }
    }else {
        for (let siger in sigers ){
            triplet = sealet + sigers[siger].qb64b()
            this.logger.addVre(dgKey_, triplet)
        }
    }

    }




    /**
     * @description  Processes potential duplicitous events in PDELs

        Handles duplicity detection and logging if duplicitous

     * @param {*} serder 
     * @param {*} sigers 
     */
    duplicity(serder: any, sigers: any){

        // @ts-expect-error ts-migrate(2461) FIXME: Type 'null' is not an array type.
        let [prefixer,pre,ked,ilk,sn,dig] = null
        let ked1 = serder.ked

        try{
            prefixer = new Prefixer(null,null,null,null,null,ked["pre"])
        }catch(err){
throw new Error(`Invalid pre = ${ked["pre"]}.`);
        }

        pre = prefixer.qb64
        ked = serder.ked
        ilk = ked["ilk"]

        try{
            sn = parseInt(ked["sn"], 16)
        }catch(err){
            throw new Error(`Invalid sn = ${ked["sn"]}`)
        }
        dig = serder.dig



        if (ilk === Ilks.icp){
            // @ts-expect-error ts-migrate(2552) FIXME: Cannot find name 'siger'. Did you mean 'sigers'?
            let kever = new Kever(serder, siger, (self as any).logger);
        }else {
            {}
        }

    }
}

module.exports = {Kevery}