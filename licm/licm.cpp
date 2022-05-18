#include "llvm/Pass.h"
#include "llvm/Analysis/LoopPass.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/Instruction.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/Constant.h"
#include "llvm/IR/Dominators.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/IR/LegacyPassManager.h"
#include "llvm/Transforms/IPO/PassManagerBuilder.h"
using namespace llvm;

namespace {
  struct LicmPass : public LoopPass {
    static char ID;
    LicmPass() : LoopPass(ID) {}

    virtual bool runOnLoop(Loop *L, LPPassManager &LPM) {
      bool changed = false;
      BasicBlock* preheader = L->getLoopPreheader();
			if (!preheader) {
				return changed;
			}

      for (auto *B : L->getBlocksVector()) {
        for (auto &I : *B){
          auto *op = dyn_cast<Instruction>(&I);
          bool immediate_loopbody = true;
          for(auto subLoop : L->getSubLoops()){
            if(subLoop->contains(op)){
              immediate_loopbody = false;
            }
          }
          if(I.mayHaveSideEffects() && !immediate_loopbody) continue;
          if(L->hasLoopInvariantOperands(op)){
            op->moveBefore(&preheader->back());
            changed = true;
          }
        }
      }

      // LoopInfo& LI = getAnalysis<LoopInfo>();
      
      return changed;
    }
  };
}

char LicmPass::ID = 0;

// Automatically enable the pass.
// http://adriansampson.net/blog/clangpass.html
static void registerLicmPass(const PassManagerBuilder &,
                         legacy::PassManagerBase &PM) {
  PM.add(new LicmPass());
}
static RegisterStandardPasses
  RegisterMyPass(PassManagerBuilder::EP_EarlyAsPossible,
                 registerLicmPass);
