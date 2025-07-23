import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DashboardCurrentDocuments } from './dashboard-current-documents';

describe('DashboardCurrentDocuments', () => {
  let component: DashboardCurrentDocuments;
  let fixture: ComponentFixture<DashboardCurrentDocuments>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DashboardCurrentDocuments]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DashboardCurrentDocuments);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
